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
from agent_system.subagents.employee_analytics_agent import EmployeeAnalyticsAgent
from agent_system.subagents.project_analytics_agent import ProjectAnalyticsAgent
from agent_system.subagents.task_analytics_agent import TaskAnalyticsAgent
from agent_system.subagents.code_interpreter_agent import CodeInterpreterAgent
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
        
        # Initialize sub-agents (4 communication + 3 analytics + 1 code interpreter)
        self.logger.log("Initializing sub-agents with Agents SDK...")
        self.subagents = {
            "calendar": CalendarAgent(logger),
            "email": EmailAgent(logger),
            "report_writer": ReportWriterAgent(logger),
            "whatsapp": WhatsAppAgent(logger),
            "employee_analytics": EmployeeAnalyticsAgent(logger),
            "project_analytics": ProjectAnalyticsAgent(logger),
            "task_analytics": TaskAnalyticsAgent(logger),
            "code_interpreter": CodeInterpreterAgent(logger)
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
        
        employee_analytics_tool = self.subagents["employee_analytics"].as_tool(
            tool_name="employee_analytics_expert",
            tool_description="Query employee performance, productivity, hours worked, and client distribution from DDMac Analytics database"
        )
        
        project_analytics_tool = self.subagents["project_analytics"].as_tool(
            tool_name="project_analytics_expert",
            tool_description="Analyze project budgets, progress, team allocation, and variance from DDMac Analytics database"
        )
        
        task_analytics_tool = self.subagents["task_analytics"].as_tool(
            tool_name="task_analytics_expert",
            tool_description="Track task-level efficiency, foreman progress, budget variance, and completion status from DDMac Analytics database"
        )
        
        code_interpreter_tool = self.subagents["code_interpreter"].as_tool(
            tool_name="code_interpreter_expert",
            tool_description="Create data visualizations, charts, plots, CSV/Excel files, and perform data analysis using Python code execution"
        )
        
        self.logger.log("Sub-agents converted to tools:")
        self.logger.log("  - calendar_expert (Calendar Agent)")
        self.logger.log("  - email_expert (Email Agent)")
        self.logger.log("  - report_expert (Report Writer Agent)")
        self.logger.log("  - whatsapp_expert (WhatsApp Agent)")
        self.logger.log("  - employee_analytics_expert (Employee Analytics Agent)")
        self.logger.log("  - project_analytics_expert (Project Analytics Agent)")
        self.logger.log("  - task_analytics_expert (Task Analytics Agent)")
        self.logger.log("  - code_interpreter_expert (Code Interpreter Agent)")
        
        # Build orchestrator instructions
        instructions = self._get_orchestrator_instructions()
        
        # Create orchestrator with profile-based optimization
        orchestrator = Agent(
            name="Orchestrator Agent",
            instructions=instructions,
            model=profile.model,
            model_settings=profile.to_model_settings(),  # Dynamic reasoning + verbosity!
            tools=[
                calendar_tool, 
                email_tool, 
                report_tool, 
                whatsapp_tool,
                employee_analytics_tool,
                project_analytics_tool,
                task_analytics_tool,
                code_interpreter_tool
            ],
            tool_use_behavior="run_llm_again"  # Process tool results before responding
        )
        
        self.logger.log(f"Orchestrator Agent created for {complexity} complexity with 8 specialist tool-agents")
        
        return orchestrator
    
    def _get_orchestrator_instructions(self) -> str:
        """
        Get compressed orchestrator instructions for DiddyMac (4 communication agents)
        
        Returns:
            Instruction string
        """
        return """You are the DiddyMac Orchestrator Agent coordinating specialized communication and analytics agents to complete tasks.

CORE BEHAVIOR: Execute proactively with intelligent defaults. Don't ask, DO. Report completed actions.

AVAILABLE TOOLS (8 specialist agents):

COMMUNICATION AGENTS:
- calendar_expert: Google Calendar + Meet (schedule, create events, manage invitations)
- email_expert: Gmail + Docs (send, draft, read, share docs with email)
- report_expert: Google Docs + Drive (create documents, folders, set sharing to "anyone with link")
- whatsapp_expert: WhatsApp (send confirmations, status updates)

ANALYTICS AGENTS (DDMac Analytics Database):
- employee_analytics_expert: Employee performance, productivity, hours, client distribution
- project_analytics_expert: Project budgets, progress, team allocation, variance analysis
- task_analytics_expert: Task efficiency, foreman progress, budget variance, completion tracking

DATA & VISUALIZATION:
- code_interpreter_expert: Create charts, plots, CSV/Excel files, data analysis with Python

WHEN TO USE EACH EXPERT:
- Calendar/meeting questions or scheduling → calendar_expert
- Email questions or sending → email_expert
- Creating text documents, folders, reports → report_expert
- Confirmations → whatsapp_expert
- Employee performance/hours/productivity questions → employee_analytics_expert
- Project budget/progress/team questions → project_analytics_expert
- Task efficiency/variance/foreman progress questions → task_analytics_expert
- Charts, plots, visualizations, CSV/Excel files → code_interpreter_expert

WORKFLOW FOR REPORTS WITH VISUALIZATIONS:
1. Use analytics agents to get data
2. Use code_interpreter_expert to create charts/CSV files
3. Use report_expert to create Google Drive folder and Doc
4. Upload visualization files to the folder (via report_expert)
5. Share folder link with "anyone with link can view"
6. Email/WhatsApp the folder link to user

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

