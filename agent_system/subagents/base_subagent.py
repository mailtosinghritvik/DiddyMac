import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from composio import Composio
from composio_openai_agents import OpenAIAgentsProvider
from dotenv import load_dotenv
import sys
from agents import Agent, function_tool, RunContextWrapper, trace

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()

# Import configuration
from config.agent_config import AgentOptimizationProfile, get_agent_profile

class BaseSubAgent(ABC):
    """
    Base class for all specialized sub-agents using OpenAI Agents SDK
    Implements hierarchical delegation with isolated contexts
    
    Sub-agents:
    - Use Agents SDK Agent class
    - Have their own isolated context window
    - Use specific Composio toolkits
    - Return synthesized results via tool_use_behavior
    """
    
    def __init__(
        self,
        name: str,
        toolkits: Optional[List[str]] = None,
        description: str = "",
        logger=None,
        custom_tools: Optional[List] = None,
        agent_type: str = None,
        profile: AgentOptimizationProfile = None
    ):
        """
        Initialize base sub-agent with optimization profile support
        
        Args:
            name: Agent name
            toolkits: List of Composio toolkits to use (e.g., ["GMAIL", "GOOGLECALENDAR"])
            description: Agent description/capabilities
            logger: Optional logger instance
            custom_tools: Optional list of custom function tools (e.g., @function_tool decorated)
            agent_type: Type of agent for profile lookup (calendar, email, etc.)
            profile: Custom profile override (optional)
        """
        self.name = name
        self.toolkits = toolkits or []
        self.custom_tools = custom_tools or []
        self.description = description
        self.logger = logger
        self.user_id = "default"
        
        # Get optimization profile
        if profile:
            self.profile = profile
        elif agent_type:
            self.profile = get_agent_profile(agent_type)
        else:
            # Fallback default (medium settings)
            self.profile = AgentOptimizationProfile(
                model="gpt-5",
                reasoning_effort="medium",
                verbosity="medium",
                max_turns=10
            )
        
        if self.logger:
            self.logger.log(f"Initializing {self.name} with Agents SDK")
            self.logger.log(f"Optimization Profile: {self.profile.model}, reasoning={self.profile.reasoning_effort}, verbosity={self.profile.verbosity}")
            if self.toolkits:
                self.logger.log(f"Composio Toolkits: {', '.join(self.toolkits)}")
            if self.custom_tools:
                tool_names = [getattr(t, '__name__', 'custom_tool') for t in self.custom_tools]
                self.logger.log(f"Custom Tools: {', '.join(tool_names)}")
        
        # Initialize Composio with OpenAI Agents Provider (only if using Composio toolkits)
        if self.toolkits:
            self.composio = Composio(provider=OpenAIAgentsProvider())
            self.composio_tools = self._get_composio_tools()
        else:
            self.composio = None
            self.composio_tools = []
        
        if self.logger:
            self.logger.log(f"Loaded {len(self.composio_tools)} Composio tools")
            if self.custom_tools:
                self.logger.log(f"Loaded {len(self.custom_tools)} custom tools")
        
        # Combine all tools (Composio + custom)
        all_tools = self.composio_tools + self.custom_tools
        
        # Create the Agent instance with combined tools
        self.agent = self._create_agent(all_tools)
        
        if self.logger:
            self.logger.log(f"{self.name} initialized successfully")
    
    def _get_composio_tools(self) -> List:
        """
        Get Composio tools for this agent's toolkits
        
        Returns:
            List of Composio function tools
        """
        try:
            # Get tools from Composio for specified toolkits
            tools = self.composio.tools.get(
                user_id=self.user_id,
                toolkits=self.toolkits,
                limit=100
            )
            
            if self.logger:
                self.logger.log(f"Retrieved {len(tools)} tools from Composio for {', '.join(self.toolkits)}")
            
            return tools
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error loading Composio tools: {str(e)}", "ERROR")
            return []
    
    @abstractmethod
    def get_specialized_instructions(self) -> str:
        """
        Get specialized instructions for this sub-agent
        Must be implemented by each subclass
        
        Returns:
            Specialized instructions string
        """
        pass
    
    def _get_full_instructions(self) -> str:
        """
        Build compressed instructions combining base and specialized instructions
        
        Returns:
            Complete instruction string
        """
        base_instructions = f"""You are {self.name}, a specialized AI agent.

PURPOSE: {self.description}

CAPABILITIES: {', '.join(self.toolkits)} tools via Composio.

CORE INSTRUCTIONS:
1. Focus on assigned task
2. Use available tools efficiently
3. Try alternatives on errors
4. Provide clear, synthesized summaries
5. Verify tool outputs

RESPONSE: State actions taken, summarize results, include relevant details, note issues/resolutions."""
        
        specialized = self.get_specialized_instructions()
        
        return base_instructions + "\n\n" + specialized
    
    def _create_agent(self, tools_list: List) -> Agent:
        """
        Create the Agent SDK agent instance with provided tools and optimization profile
        
        Args:
            tools_list: Combined list of tools (Composio + custom)
        
        Returns:
            Configured Agent instance with optimized ModelSettings
        """
        # Build complete instructions
        instructions = self._get_full_instructions()
        
        # Create Agent with profile-based optimization
        agent = Agent(
            name=self.name,
            instructions=instructions,
            model=self.profile.model,
            model_settings=self.profile.to_model_settings(),  # Dynamic reasoning + verbosity!
            tools=tools_list,  # Use combined tools (Composio + custom)
            tool_use_behavior="run_llm_again"  # Default: run LLM again after tools
        )
        
        if self.logger:
            self.logger.log(f"Created Agent instance for {self.name}")
            self.logger.log(f"Model: {self.profile.model}, Reasoning: {self.profile.reasoning_effort}, Verbosity: {self.profile.verbosity}")
            self.logger.log(f"Total tools configured: {len(tools_list)} ({len(self.composio_tools)} Composio + {len(self.custom_tools)} custom)")
        
        return agent
    
    def get_agent(self) -> Agent:
        """
        Get the underlying Agent instance for use as a tool
        
        Returns:
            Agent instance
        """
        return self.agent
    
    def as_tool(self, tool_name: Optional[str] = None, tool_description: Optional[str] = None):
        """
        Convert this sub-agent to a tool for orchestrator
        
        Args:
            tool_name: Custom tool name (defaults to snake_case of agent name)
            tool_description: Custom tool description (defaults to agent description)
        
        Returns:
            Tool representation of this agent
        """
        name = tool_name or self.name.lower().replace(" ", "_")
        desc = tool_description or self.description
        
        if self.logger:
            self.logger.log(f"Converting {self.name} to tool: {name}")
        
        return self.agent.as_tool(
            tool_name=name,
            tool_description=desc
        )
    
    async def run(self, task: str, context: Optional[Any] = None, max_turns: int = 10) -> Any:
        """
        Run the agent on a task using Runner
        
        Args:
            task: Task description
            context: Optional context object
            max_turns: Maximum turns for agent
        
        Returns:
            RunResult from agent execution
        """
        from agents import Runner
        
        if self.logger:
            self.logger.log(f"=== {self.name.upper()} RUNNING ===")
            self.logger.log(f"Task: {task}")
            self.logger.log(f"Max turns: {max_turns}")
        
        try:
            # Run the agent with Responses API configuration
            # Wrap in trace for OpenAI dashboard visibility
            with trace(f"{self.name}"):
                result = await Runner.run(
                    starting_agent=self.agent,
                    input=task,
                    context=context,
                    max_turns=max_turns,
                )
            
            if self.logger:
                self.logger.log(f"{self.name} completed successfully")
                self.logger.log(f"Final output: {result.final_output[:200]}..." if len(str(result.final_output)) > 200 else f"Final output: {result.final_output}")
            
            return result
        
        except Exception as e:
            error_msg = f"{self.name} error: {str(e)}"
            if self.logger:
                self.logger.log(error_msg, "ERROR")
            raise
    
    def process(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a task (backward compatible synchronous wrapper)
        
        Args:
            task_description: Description of the task to complete
            context: Optional context dictionary with additional info
        
        Returns:
            Dictionary with success status and result
        """
        import asyncio
        
        if self.logger:
            self.logger.log(f"=== {self.name.upper()} PROCESSING (SYNC WRAPPER) ===")
            self.logger.log(f"Task: {task_description}")
        
        try:
            # Build input with context if provided
            input_text = task_description
            if context:
                input_text += f"\n\nContext: {context}"
            
            # Run async method in sync context
            result = asyncio.run(self.run(input_text))
            
            return {
                "success": True,
                "agent": self.name,
                "result": str(result.final_output)
            }
        
        except Exception as e:
            error_msg = f"{self.name} error: {str(e)}"
            if self.logger:
                self.logger.log(error_msg, "ERROR")
            
            return {
                "success": False,
                "agent": self.name,
                "error": str(e),
                "result": f"Failed to complete task: {str(e)}"
            }

