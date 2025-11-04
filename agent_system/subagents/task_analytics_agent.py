from .base_subagent import BaseSubAgent
from agent_system.tools.analytics_tools import (
    get_task_variance_analysis,
    get_task_progress_status,
    update_foreman_task_progress,
    get_task_efficiency_summary
)

class TaskAnalyticsAgent(BaseSubAgent):
    """
    Specialized agent for task-level analytics and efficiency tracking
    Uses: Custom DDMac Analytics Supabase tools
    Configured with GPT-5-mini, low reasoning effort, medium verbosity
    """
    
    def __init__(self, logger=None):
        super().__init__(
            name="Task Analytics Agent",
            toolkits=[],  # No Composio toolkits - using custom analytics tools
            custom_tools=[
                get_task_variance_analysis,
                get_task_progress_status,
                update_foreman_task_progress,
                get_task_efficiency_summary
            ],
            description="Specialized agent for task-level variance analysis, foreman progress tracking, and efficiency metrics from DDMac Analytics database",
            logger=logger,
            agent_type="task_analytics"
        )
        
        if logger:
            logger.log("Task Analytics Agent initialized with optimization profile")
            logger.log("Tools: 4 custom DDMac Analytics Supabase tools")
    
    def get_specialized_instructions(self) -> str:
        """
        Task analytics-specific instructions
        """
        return """TASK ANALYTICS OPERATIONS:
- Analyze task-level budget variances
- Track foreman progress updates
- Calculate task efficiency scores
- Update and monitor task completion status

AVAILABLE TOOLS:
- get_task_variance_analysis: Tasks over/under budget with variance percentages
- get_task_progress_status: Foreman progress for all tasks in a project
- update_foreman_task_progress: Update foreman progress percentage for a task
- get_task_efficiency_summary: Efficiency ratings (actual/estimated ratios)

DATA SOURCE: DDMac Analytics Supabase (separate from communication database)

OUTPUT: Provide task-level insights with variance analysis, efficiency scores, and foreman progress comparisons. Identify high/low performing tasks clearly."""

