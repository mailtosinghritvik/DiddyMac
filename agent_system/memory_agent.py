import os
import sys
from typing import Dict, Any, List
from dotenv import load_dotenv
from pydantic import BaseModel
from agents import Agent, Runner, trace

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Import configuration for optimization profiles
from config.agent_config import AGENT_PROFILES

# Pydantic models for structured outputs
class IntentClassification(BaseModel):
    """Structured output for intent classification with dual intent support"""
    primary_intent: str  # "rule_only", "action_only", or "both"
    has_rule: bool  # True if message contains a rule to create
    has_action: bool  # True if message contains an action to execute
    rule_description: str = ""  # Brief description of the rule (if has_rule)
    action_description: str = ""  # Brief description of the action (if has_action)
    reasoning: str
    confidence: float  # 0.0 to 1.0

class RuleData(BaseModel):
    """Structured output for rule extraction"""
    rule_maker: str
    rule_org: str
    rule_instruction: str
    reasoning: str

class RelevantRulesOutput(BaseModel):
    """Structured output for rule filtering"""
    relevant_rule_indices: List[int]  # 1-based indices
    reasoning: str

class TaskComplexity(BaseModel):
    """Structured output for task complexity classification"""
    complexity: str  # "simple", "medium", "complex"
    reasoning: str
    suggested_reasoning_effort: str  # "minimal", "low", "medium"
    suggested_max_turns: int  # 15, 30, or 45

class MemoryAgent:
    """
    Memory Agent using OpenAI Agents SDK with GPT-5-mini
    Handles intent classification, rule creation, and rule filtering
    Uses structured outputs for reliability
    """
    
    def __init__(self, supabase_client, logger):
        """
        Initialize Memory Agent
        
        Args:
            supabase_client: SupabaseClient instance for database operations
            logger: AgentLogger instance for logging
        """
        self.supabase = supabase_client
        self.logger = logger
        
        self.logger.log("Initializing Memory Agent with GPT-5-mini and Agents SDK")
        
        # Create specialized agents for different memory tasks
        self._create_agents()
        
        self.logger.log("Memory Agent initialized successfully")
    
    def _create_agents(self):
        """Create specialized agents for memory tasks with optimization profiles"""
        
        # Get profiles for all memory sub-agents
        intent_profile = AGENT_PROFILES["intent_classifier"]
        rule_profile = AGENT_PROFILES["rule_extractor"]
        filter_profile = AGENT_PROFILES["rule_filter"]
        complexity_profile = AGENT_PROFILES["complexity_classifier"]
        
        # Intent classification agent with dual intent support (minimal reasoning)
        self.intent_classifier = Agent(
            name="Intent Classifier",
            instructions="""You are an intent classification expert with dual intent detection support.

Analyze messages to identify THREE possibilities:

1. RULE_ONLY: Only creating a rule/preference (no immediate action)
   - Keywords: "remember", "always", "from now on", "never", "make sure to", "prefer"
   - No immediate action verbs
   - Examples:
     * "Remember to always CC john@example.com on emails"
     * "From now on, schedule meetings in the afternoon"

2. ACTION_ONLY: Only executing a task (no rule creation)
   - Immediate action verbs: "send", "schedule", "create", "do"
   - Time-specific: "now", "today", "tomorrow"
   - No "remember" or "always" keywords
   - Examples:
     * "Send email to team@company.com"
     * "Schedule meeting tomorrow at 3pm"

3. BOTH: Contains BOTH rule AND action in same message
   - Has rule keywords (remember, always) AND action verbs (send, schedule)
   - Often connected with "and", "also", "then"
   - Examples:
     * "Remember to CC john on emails, and send an email to the team"
       → Rule: CC john on emails / Action: Send email to team
     * "From now on add agendas to meetings, and schedule Friday's review"
       → Rule: Add agendas / Action: Schedule Friday meeting
     * "Always use formal tone, and draft email to client@example.com"
       → Rule: Use formal tone / Action: Draft email to client

OUTPUT REQUIREMENTS:
- primary_intent: "rule_only", "action_only", or "both"
- has_rule: True if message contains rule to create
- has_action: True if message contains action to execute
- rule_description: What rule to create (if has_rule=True)
- action_description: What action to do (if has_action=True)
- reasoning: Explain why you classified this way
- confidence: 0.0 to 1.0

CRITICAL: When extracting rule_description from dual intent:
- Extract ONLY the preference/rule clause (e.g., "CC john on emails")
- Do NOT include the action/task part
- Separate at conjunctions: "and", "also", "then"
- Example: "Remember to CC john, and send email to team"
  → rule_description: "CC john on all emails"
  → action_description: "Send email to team"

Parse intelligently using keywords, conjunctions, and context.""",
            model=intent_profile.model,
            model_settings=intent_profile.to_model_settings(),
            output_type=IntentClassification
        )
        self.logger.log(f"Created Intent Classifier ({intent_profile.model}, reasoning={intent_profile.reasoning_effort}, verbosity={intent_profile.verbosity})")
        
        # Rule extraction agent (low reasoning, low verbosity)
        self.rule_extractor = Agent(
            name="Rule Extractor",
            instructions="""You are a rule extraction specialist. Extract structured rule information from user messages.

Your task is to:
1. Identify who is creating the rule (rule_maker)
2. Categorize the rule (rule_org): e.g., 'email_preferences', 'meeting_scheduling', 'communication_style', 'workflow', etc.
3. Write a clear, actionable instruction (rule_instruction)
4. Explain your reasoning

Make the rule_instruction clear, specific, and actionable so it can be applied in future contexts.""",
            model=rule_profile.model,
            model_settings=rule_profile.to_model_settings(),
            output_type=RuleData
        )
        self.logger.log(f"Created Rule Extractor ({rule_profile.model}, reasoning={rule_profile.reasoning_effort}, verbosity={rule_profile.verbosity})")
        
        # Rule filtering agent (low reasoning, low verbosity)
        self.rule_filter = Agent(
            name="Rule Filter",
            instructions="""You are a rule relevance expert. Given a user request and a list of rules, identify which rules are relevant.

Return the 1-based indices of relevant rules. Only include rules that directly apply to the current request.

Be selective - only include rules that are truly relevant to executing the current task.""",
            model=filter_profile.model,
            model_settings=filter_profile.to_model_settings(),
            output_type=RelevantRulesOutput
        )
        self.logger.log(f"Created Rule Filter ({filter_profile.model}, reasoning={filter_profile.reasoning_effort}, verbosity={filter_profile.verbosity})")
        
        # Complexity classifier for dynamic reasoning (minimal reasoning)
        self.complexity_classifier = Agent(
            name="Complexity Classifier",
            instructions="""Classify task complexity to optimize reasoning effort.

SIMPLE (minimal reasoning, 15 turns):
- Single, straightforward action with explicit parameters
- Examples: "Send email to john@example.com about meeting"
          "Schedule meeting tomorrow at 3pm with team"
          "Send WhatsApp confirmation"

MEDIUM (low reasoning, 30 turns):  
- Multi-step task OR needs some inference
- Examples: "Send email to team and CC relevant people per rules"
          "Schedule meeting at convenient afternoon time"
          "Create document and share via email"

COMPLEX (medium reasoning, 45 turns):
- Multi-agent coordination OR significant inference
- Examples: "Create report and email stakeholders"
          "Find best time across calendars and schedule"
          "Draft comprehensive proposal with research"

Output complexity level, reasoning, suggested_reasoning_effort, and suggested_max_turns.""",
            model=complexity_profile.model,
            model_settings=complexity_profile.to_model_settings(),
            output_type=TaskComplexity
        )
        self.logger.log(f"Created Complexity Classifier ({complexity_profile.model}, reasoning={complexity_profile.reasoning_effort}, verbosity={complexity_profile.verbosity})")
    
    async def classify_intent_async(self, input_body: Dict[str, Any]) -> IntentClassification:
        """
        Classify whether the input has rule creation, action execution, or both
        
        Args:
            input_body: The input body containing current message and history
        
        Returns:
            IntentClassification object with primary_intent, has_rule, has_action, etc.
        """
        self.logger.log("Classifying intent with GPT-5-mini (minimal reasoning, dual intent support)...")
        
        current_message = input_body["current_message_input"]["content"]
        
        try:
            with trace("Intent-Classifier"):
                result = await Runner.run(
                    starting_agent=self.intent_classifier,
                    input=f"Classify this message: \"{current_message}\"",
                    max_turns=1
                )
            
            classification = result.final_output_as(IntentClassification)
            
            self.logger.log(f"Primary intent: {classification.primary_intent}")
            self.logger.log(f"Has rule: {classification.has_rule}")
            self.logger.log(f"Has action: {classification.has_action}")
            if classification.has_rule:
                self.logger.log(f"Rule: {classification.rule_description}")
            if classification.has_action:
                self.logger.log(f"Action: {classification.action_description}")
            self.logger.log(f"Confidence: {classification.confidence}")
            self.logger.log(f"Reasoning: {classification.reasoning}")
            
            return classification
        
        except Exception as e:
            self.logger.log(f"Error classifying intent: {str(e)}", "ERROR")
            # Default to action_execution to avoid breaking the pipeline
            return IntentClassification(
                primary_intent="action_only",
                has_rule=False,
                has_action=True,
                reasoning=f"Error in classification, defaulting to action_only: {str(e)}",
                confidence=0.5
            )
    
    async def classify_complexity_async(self, input_body: Dict[str, Any]) -> TaskComplexity:
        """
        Classify task complexity for dynamic reasoning optimization
        
        Args:
            input_body: The input body containing current message
        
        Returns:
            TaskComplexity object with optimization suggestions
        """
        self.logger.log("Classifying task complexity for optimization...")
        
        current_message = input_body["current_message_input"]["content"]
        
        try:
            with trace("Complexity-Classifier"):
                result = await Runner.run(
                    starting_agent=self.complexity_classifier,
                    input=f"Classify complexity: \"{current_message}\"",
                    max_turns=1
                )
            
            complexity = result.final_output_as(TaskComplexity)
            
            self.logger.log(f"Task complexity: {complexity.complexity}")
            self.logger.log(f"Suggested reasoning: {complexity.suggested_reasoning_effort}")
            self.logger.log(f"Suggested max turns: {complexity.suggested_max_turns}")
            self.logger.log(f"Reasoning: {complexity.reasoning}")
            
            return complexity
        
        except Exception as e:
            self.logger.log(f"Error classifying complexity: {str(e)}", "ERROR")
            # Default to medium for safety
            return TaskComplexity(
                complexity="medium",
                reasoning=f"Error in classification, defaulting to medium: {str(e)}",
                suggested_reasoning_effort="low",
                suggested_max_turns=30
            )
    
    async def extract_rule_async(self, input_body: Dict[str, Any], rule_description: str) -> Dict[str, str]:
        """
        Extract rule details from ONLY the rule portion (not full message)
        
        Args:
            input_body: The input body containing the message
            rule_description: The rule part from intent classifier (NOT full message!)
        
        Returns:
            Dictionary with rule_maker, rule_org, and rule_instruction
        """
        self.logger.log("Extracting rule with GPT-5-mini (low reasoning)...")
        
        sender = input_body["current_message_input"]["sender"]
        
        prompt = f"""Extract structured rule information from this rule statement ONLY.

Rule Statement (ONLY the rule, NOT any action): "{rule_description}"
Sender: "{sender}"

Extract:
- rule_maker: Who is creating this rule
- rule_org: Category (email_preferences, meeting_scheduling, communication_style, etc.)
- rule_instruction: Clear, actionable rule instruction

CRITICAL: Do NOT include any immediate action tasks. Only the persistent rule/preference.

Provide structured rule information."""
        
        try:
            with trace("Rule-Extractor"):
                result = await Runner.run(
                    starting_agent=self.rule_extractor,
                    input=prompt,
                    max_turns=1
                )
            
            rule_data = result.final_output_as(RuleData)
            
            self.logger.log(f"Rule extracted: {rule_data.rule_instruction}")
            self.logger.log(f"Category: {rule_data.rule_org}")
            self.logger.log(f"Reasoning: {rule_data.reasoning}")
            
            return {
                "rule_maker": rule_data.rule_maker,
                "rule_org": rule_data.rule_org,
                "rule_instruction": rule_data.rule_instruction
            }
        
        except Exception as e:
            self.logger.log(f"Error extracting rule: {str(e)}", "ERROR")
            # Return a default rule structure
            current_message = input_body["current_message_input"]["content"]
            return {
                "rule_maker": sender,
                "rule_org": "general",
                "rule_instruction": current_message
            }
    
    async def filter_relevant_rules_async(
        self,
        all_rules: List[Dict[str, Any]],
        input_body: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter rules that are relevant to the current input
        
        Args:
            all_rules: All rules from the database
            input_body: The input body
        
        Returns:
            List of relevant rules
        """
        if not all_rules:
            self.logger.log("No rules found in database")
            return []
        
        self.logger.log(f"Filtering relevant rules from {len(all_rules)} total rules with GPT-5-mini...")
        
        current_message = input_body["current_message_input"]["content"]
        
        rules_text = "\n".join([
            f"Rule {i+1}: {rule['rule_instruction']} (Category: {rule.get('rule_org', 'N/A')})"
            for i, rule in enumerate(all_rules)
        ])
        
        prompt = f"""Identify which rules are relevant to this request:

User Request: "{current_message}"

Available Rules:
{rules_text}

Return the indices of relevant rules (1-based). Be selective."""
        
        try:
            with trace("Rule-Filter"):
                result = await Runner.run(
                    starting_agent=self.rule_filter,
                    input=prompt,
                    max_turns=1
                )
            
            filter_output = result.final_output_as(RelevantRulesOutput)
            
            # Convert 1-based indices to 0-based and get rules
            relevant_rules = [
                all_rules[i-1] for i in filter_output.relevant_rule_indices
                if 0 < i <= len(all_rules)
            ]
            
            self.logger.log(f"Found {len(relevant_rules)} relevant rules")
            self.logger.log(f"Reasoning: {filter_output.reasoning}")
            
            return relevant_rules
        
        except Exception as e:
            self.logger.log(f"Error filtering rules: {str(e)}", "ERROR")
            # Return all rules if filtering fails
            return all_rules
    
    async def process_async(self, input_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main async processing method for Memory Agent with dual intent support
        
        Args:
            input_body: The input body containing current message and history
        
        Returns:
            Dictionary with type and relevant data (supports dual intent)
        """
        self.logger.log("=== MEMORY AGENT PROCESSING (AGENTS SDK, DUAL INTENT) ===")
        
        # Classify intent (now returns full classification object)
        classification = await self.classify_intent_async(input_body)
        
        # Classify complexity for optimization
        complexity = await self.classify_complexity_async(input_body)
        
        # Fetch all rules from database
        all_rules = self.supabase.get_all_rules()
        self.logger.log(f"Fetched {len(all_rules)} rules from database")
        
        created_rule = None
        
        # Handle rule creation if present
        if classification.has_rule:
            self.logger.log("📋 RULE CREATION DETECTED")
            self.logger.log(f"Rule to create: {classification.rule_description}")
            
            # Extract and save rule using ONLY the rule_description (not full message)
            rule_data = await self.extract_rule_async(
                input_body,
                rule_description=classification.rule_description  # Pass only rule part
            )
            
            # Insert rule into database
            created_rule = self.supabase.insert_rule(
                rule_maker=rule_data["rule_maker"],
                rule_org=rule_data["rule_org"],
                rule_instruction=rule_data["rule_instruction"]
            )
            
            self.logger.log(f"✅ Rule created with ID: {created_rule.get('id')}")
            self.logger.log(f"Rule: {created_rule.get('rule_instruction')}")
            
            # Refresh rules to include the newly created one
            all_rules = self.supabase.get_all_rules()
            self.logger.log(f"Rules refreshed: {len(all_rules)} total (including new rule)")
        
        # Handle action execution if present
        if classification.has_action:
            self.logger.log("⚡ ACTION EXECUTION DETECTED")
            if classification.has_rule:
                self.logger.log("📋 Dual intent: Will execute action with newly created rule")
            
            # Filter relevant rules (includes newly created rule if applicable)
            relevant_rules = await self.filter_relevant_rules_async(all_rules, input_body)
            
            # Determine result type
            if classification.has_rule:
                result_type = "both"  # Both rule and action
            else:
                result_type = "action_execution"  # Action only
            
            return {
                "type": result_type,
                "relevant_rules": relevant_rules,
                "input_body": input_body,
                "rule_created": created_rule,  # Include if rule was created
                "action_description": classification.action_description,
                "complexity": complexity.complexity,
                "suggested_reasoning_effort": complexity.suggested_reasoning_effort,
                "suggested_max_turns": complexity.suggested_max_turns
            }
        
        # Rule only, no action
        self.logger.log("📋 RULE ONLY: No action to execute")
        return {
            "type": "rule_creation",
            "rule": created_rule,
            "message": "New rule created successfully"
        }

