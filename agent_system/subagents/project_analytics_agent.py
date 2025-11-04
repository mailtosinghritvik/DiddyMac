from .base_subagent import BaseSubAgent
from agent_system.tools.analytics_tools import (
    get_project_overview,
    get_project_budget_analysis,
    get_all_projects_status,
    get_project_team_hours
)

class ProjectAnalyticsAgent(BaseSubAgent):
    """
    Specialized agent for project analytics and budget tracking
    Uses: Custom DDMac Analytics Supabase tools
    Configured with GPT-5-mini, low reasoning effort, medium verbosity
    """
    
    def __init__(self, logger=None):
        super().__init__(
            name="Project Analytics Agent",
            toolkits=[],  # No Composio toolkits - using custom analytics tools
            custom_tools=[
                get_project_overview,
                get_project_budget_analysis,
                get_all_projects_status,
                get_project_team_hours
            ],
            description="Specialized agent for project budget analysis, progress tracking, and team allocation insights from DDMac Analytics database",
            logger=logger,
            agent_type="project_analytics"
        )
        
        if logger:
            logger.log("Project Analytics Agent initialized with optimization profile")
            logger.log("Tools: 4 custom DDMac Analytics Supabase tools")
    
    def get_specialized_instructions(self) -> str:
        """
        Project analytics-specific instructions
        """
        return """PROJECT ANALYTICS OPERATIONS:
- Analyze project budgets (estimated vs actual hours)
- Track project completion and progress
- Review team allocation per project
- Identify budget variances and overruns

AVAILABLE TOOLS:
- get_project_overview: Comprehensive project metrics (budget, completion, variance)
- get_project_budget_analysis: Detailed budget breakdown by task
- get_all_projects_status: Overview of all active projects
- get_project_team_hours: Team member hours per project

DATA SOURCE: DDMac Analytics Supabase (separate from communication database)

OUTPUT: Provide budget status, variance analysis, completion percentages, and team allocation summaries. Highlight over/under budget situations clearly."""

