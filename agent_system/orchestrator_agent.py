import os
import sys
import json
from typing import Dict, Any, List
from datetime import datetime
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner, ModelSettings, trace
from utils.plan_manager import PlanManager, TaskStatus
from utils.memory_storage import MemoryStorage
from agent_system.subagents.calendar_agent import CalendarAgent
from agent_system.subagents.email_agent import EmailAgent
from agent_system.subagents.report_writer_agent import ReportWriterAgent
from agent_system.subagents.whatsapp_agent import WhatsAppAgent
from config.agent_config import get_orchestrator_profile

class OrchestratorAgent:
    """
    DiddyMac Orchestrator Agent (Agents SDK Edition)
    
    Implements the Four Pillars:
    1. Explicit Planning - Creates and maintains markdown task lists
    2. Hierarchical Delegation - Uses "agents as tools" pattern
    3. Persistent Memory - Stores intermediate results in filesystem
    4. Extreme Context Engineering - Detailed system prompts and protocols
    
    Uses GPT-5 with dynamic reasoning effort for balanced orchestration
    """
    
    def __init__(self, logger):
        """
        Initialize orchestrator agent
        
        Args:
            logger: AgentLogger instance
        """
        self.logger = logger
        
        # Initialize managers
        self.plan_manager = PlanManager()
        self.memory_storage = MemoryStorage()
        
        # Initialize sub-agents (4 communication agents only)
        self.logger.log("Initializing sub-agents with Agents SDK...")
        self.subagents = {
            "calendar": CalendarAgent(logger),
            "email": EmailAgent(logger),
            "report_writer": ReportWriterAgent(logger),
            "whatsapp": WhatsAppAgent(logger)
        }
        
        self.logger.log(f"Sub-agents initialized: {', '.join(self.subagents.keys())}")
        
        # Note: Orchestrator will be created dynamically based on task complexity
        # See _create_dynamic_orchestrator() method
        
        self.logger.log("Orchestrator Agent initialization complete (will create dynamically per request)")
        self.logger.log("Sub-agents ready to be configured as tools using 'agents as tools' pattern")
    
    def _create_dynamic_orchestrator(self, complexity: str = "MEDIUM") -> Agent:
        """
        Create orchestrator Agent with complexity-appropriate optimization settings
        
        Args:
            complexity: Task complexity (SIMPLE, MEDIUM, COMPLEX)
        
        Returns:
            Configured Agent instance with optimized settings
        """
        # Get optimization profile for this complexity level
        profile = get_orchestrator_profile(complexity)
        
        self.logger.log(f"Creating orchestrator Agent for {complexity} complexity...")
        self.logger.log(f"Profile: {profile.model}, reasoning={profile.reasoning_effort}, verbosity={profile.verbosity}, max_turns={profile.max_turns}")
        
        # Convert sub-agents to tools
        calendar_tool = self.subagents["calendar"].as_tool(
            tool_name="calendar_expert",
            tool_description="Schedule meetings, create calendar events, manage Google Calendar, and create Google Meet links"
        )
        
        email_tool = self.subagents["email"].as_tool(
            tool_name="email_expert",
            tool_description="Send emails, read inbox, draft messages, manage Gmail communications, and share/attach Google Docs documents"
        )
        
        report_tool = self.subagents["report_writer"].as_tool(
            tool_name="report_expert",
            tool_description="Create structured reports, documents, and written content in Google Docs with professional formatting"
        )
        
        whatsapp_tool = self.subagents["whatsapp"].as_tool(
            tool_name="whatsapp_expert",
            tool_description="Send WhatsApp messages and confirmations to phone numbers with concise, formatted updates"
        )
        
        self.logger.log("Sub-agents converted to tools:")
        self.logger.log("  - calendar_expert (Calendar Agent)")
        self.logger.log("  - email_expert (Email Agent)")
        self.logger.log("  - report_expert (Report Writer Agent)")
        self.logger.log("  - whatsapp_expert (WhatsApp Agent)")
        
        # Build orchestrator instructions
        instructions = self._get_orchestrator_instructions()
        
        # Create orchestrator with profile-based optimization
        orchestrator = Agent(
            name="Orchestrator Agent",
            instructions=instructions,
            model=profile.model,
            model_settings=profile.to_model_settings(),  # Dynamic reasoning + verbosity!
            tools=[calendar_tool, email_tool, report_tool, whatsapp_tool],
            tool_use_behavior="run_llm_again"  # Process tool results before responding
        )
        
        self.logger.log(f"Orchestrator Agent created for {complexity} complexity with 4 specialist tool-agents")
        
        return orchestrator
    
    def _get_orchestrator_instructions(self) -> str:
        """
        Get compressed orchestrator instructions for DiddyMac (4 communication agents)
        
        Returns:
            Instruction string
        """
        return """You are the DiddyMac Orchestrator Agent coordinating specialized communication agents to complete tasks.

CORE BEHAVIOR: Execute proactively with intelligent defaults. Don't ask, DO. Report completed actions.

AVAILABLE TOOLS (4 specialist agents):
- calendar_expert: Google Calendar + Meet (schedule, create events, manage invitations)
- email_expert: Gmail + Docs (send, draft, read, share docs with email)
- report_expert: Google Docs (create documents, reports, professional formatting)
- whatsapp_expert: WhatsApp (send confirmations, status updates)

WHEN TO USE EACH EXPERT:
- Calendar/meeting questions or scheduling → calendar_expert
- Email questions or sending → email_expert
- Creating documents → report_expert
- Confirmations → whatsapp_expert

EXECUTION PROTOCOL:
1. Analyze request + rules
2. Make smart assumptions for missing info
3. Call appropriate agents with complete instructions
4. Synthesize results
5. Report what was DONE (past tense)

SMART DEFAULTS:
- Meetings: 30-60min, afternoon (2-4pm), include Meet link
- Emails: Professional tone, auto-apply CC rules
- Recipients: Infer from context (team@, engineering@, etc.)
- Reports: Executive summary + details format

DELEGATION:
- One expert per distinct subtask
- Provide full context to each expert
- Sequential calls for dependencies (report→email, calendar→whatsapp)

ERROR HANDLING: Try alternatives, report clearly if blocked.

RESPONSE FORMAT: "I did X, Y, Z. Results: [IDs/links/specifics]. Assumptions: [if any]."

Remember: BIAS TOWARDS ACTION. Execute immediately using intelligent assumptions."""
    
    async def execute_with_runner(
        self,
        orchestrator: Agent,
        user_request: str,
        relevant_rules: List[Dict],
        message_history: Dict,
        max_turns: int = 45,
        complexity: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Execute orchestration using Agents SDK Runner with dynamic orchestrator
        
        Args:
            orchestrator: Dynamically created orchestrator agent
            user_request: The user's request
            relevant_rules: Relevant rules to apply
            message_history: Previous message context
            max_turns: Maximum turns for orchestrator (from profile)
            complexity: Task complexity level
        
        Returns:
            Execution results
        """
        self.logger.log("=== EXECUTING WITH AGENTS SDK RUNNER ===")
        self.logger.log(f"User request: {user_request}")
        self.logger.log(f"Relevant rules: {len(relevant_rules)}")
        self.logger.log(f"Max turns: {max_turns}")
        
        # Build enhanced input with rules and context
        enhanced_input = self._build_enhanced_input(user_request, relevant_rules, message_history)
        
        self.logger.log(f"Running orchestrator with GPT-5 ({complexity} complexity)...")
        
        try:
            # Run orchestrator with dynamic settings via ModelSettings
            # Wrap in trace for OpenAI dashboard visibility
            with trace(f"Orchestrator-{complexity}"):
                result = await Runner.run(
                    starting_agent=orchestrator,  # Dynamic orchestrator with optimized settings
                    input=enhanced_input,
                    max_turns=max_turns  # From profile
                )
            
            self.logger.log("Orchestrator execution completed successfully")
            self.logger.log(f"Final output: {str(result.final_output)[:500]}...")
            
            # Save execution details
            self.logger.save_json("orchestrator_run_result.json", {
                "final_output": str(result.final_output),
                "turns_used": len(result.new_items) if hasattr(result, 'new_items') else 0,
                "success": True
            })
            
            return {
                "success": True,
                "final_output": str(result.final_output),
                "turns_used": len(result.new_items) if hasattr(result, 'new_items') else 0
            }
        
        except Exception as e:
            error_msg = f"Orchestrator execution error: {str(e)}"
            self.logger.log(error_msg, "ERROR")
            
            return {
                "success": False,
                "error": str(e),
                "final_output": f"Orchestration failed: {str(e)}"
            }
    
    def _build_enhanced_input(
        self,
        user_request: str,
        relevant_rules: List[Dict],
        message_history: Dict
    ) -> str:
        """
        Build enhanced input with rules and context
        
        Args:
            user_request: User's request
            relevant_rules: Relevant rules
            message_history: Message history
        
        Returns:
            Enhanced input string
        """
        enhanced = f"USER REQUEST:\n{user_request}\n"
        
        # Add relevant rules if any
        if relevant_rules:
            enhanced += "\n\nRELEVANT RULES TO FOLLOW:\n"
            for i, rule in enumerate(relevant_rules, 1):
                enhanced += f"{i}. {rule['rule_instruction']}\n"
        
        # Add message history context with stronger emphasis
        if message_history:
            before_last = message_history.get("before_last_message_same_user_same_source_different_subject", [])
            last_diff = message_history.get("last_message_same_user_different_source", [])
            
            if before_last or last_diff:
                enhanced += "\n\nCONVERSATIONAL CONTEXT (Look at these for continuity):\n"
                enhanced += "The user has sent previous messages from the same source. Use these for context:\n\n"
                if before_last:
                    for msg in before_last[:3]:  # Limit context
                        enhanced += f"- Previous from {msg.get('source')}: \"{msg.get('input')}\"\n"
                if last_diff:
                    for msg in last_diff[:2]:  # Limit context
                        enhanced += f"- From {msg.get('source')}: \"{msg.get('input')}\"\n"
        
        return enhanced
    
    async def process_async(self, memory_output: Dict[str, Any], input_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main async orchestration process with dynamic optimization
        
        Args:
            memory_output: Output from Memory Agent (relevant rules + input + optimization params)
            input_body: Input body with current message and history
        
        Returns:
            Orchestration results
        """
        self.logger.log("=== ORCHESTRATOR AGENT PROCESSING (AGENTS SDK) ===")
        
        try:
            relevant_rules = memory_output.get("relevant_rules", [])
            current_message = input_body["current_message_input"]["content"]
            message_history = input_body.get("message_history", {})
            
            # Get complexity from memory agent
            complexity = memory_output.get("complexity", "MEDIUM")
            
            # Get profile for this complexity
            profile = get_orchestrator_profile(complexity)
            
            self.logger.log(f"🎯 Dynamic Optimization: {complexity} complexity")
            self.logger.log(f"   Model: {profile.model}, Reasoning: {profile.reasoning_effort}, Verbosity: {profile.verbosity}, Max Turns: {profile.max_turns}")
            
            # Create orchestrator with complexity-appropriate settings
            dynamic_orchestrator = self._create_dynamic_orchestrator(complexity)
            
            # Run with dynamic orchestrator and profile settings
            result = await self.execute_with_runner(
                orchestrator=dynamic_orchestrator,
                user_request=current_message,
                relevant_rules=relevant_rules,
                message_history=message_history,
                max_turns=profile.max_turns,
                complexity=complexity
            )
            
            if result["success"]:
                self.logger.log("=== ORCHESTRATION COMPLETED SUCCESSFULLY ===")
                
                return {
                    "success": True,
                    "final_summary": result["final_output"],
                    "turns_used": result.get("turns_used", 0)
                }
            else:
                self.logger.log("=== ORCHESTRATION FAILED ===", "ERROR")
                
                return {
                    "success": False,
                    "error": result.get("error"),
                    "message": "Orchestration failed"
                }
        
        except Exception as e:
            error_msg = f"Orchestrator error: {str(e)}"
            self.logger.log(error_msg, "ERROR")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Orchestration failed"
            }

