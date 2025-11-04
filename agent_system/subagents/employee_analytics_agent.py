from .base_subagent import BaseSubAgent
from agent_system.tools.analytics_tools import (
    get_employee_summary,
    get_all_employees_overview,
    get_employee_client_breakdown,
    get_employee_productivity_score
)

class EmployeeAnalyticsAgent(BaseSubAgent):
    """
    Specialized agent for employee analytics and performance tracking
    Uses: Custom DDMac Analytics Supabase tools
    Configured with GPT-5-mini, low reasoning effort, medium verbosity
    """
    
    def __init__(self, logger=None):
        super().__init__(
            name="Employee Analytics Agent",
            toolkits=[],  # No Composio toolkits - using custom analytics tools
            custom_tools=[
                get_employee_summary,
                get_all_employees_overview,
                get_employee_client_breakdown,
                get_employee_productivity_score
            ],
            description="Specialized agent for employee performance analytics, productivity tracking, and workforce insights from DDMac Analytics database",
            logger=logger,
            agent_type="employee_analytics"
        )
        
        if logger:
            logger.log("Employee Analytics Agent initialized with optimization profile")
            logger.log("Tools: 4 custom DDMac Analytics Supabase tools")
    
    def get_specialized_instructions(self) -> str:
        """
        Employee analytics-specific instructions
        """
        return """EMPLOYEE ANALYTICS OPERATIONS:
- Query individual employee performance metrics
- Analyze team-wide productivity trends
- Track client time distribution per employee
- Calculate productivity scores and utilization rates

AVAILABLE TOOLS:
- get_employee_summary: Comprehensive employee metrics (hours, days, clients)
- get_all_employees_overview: Team overview with top performers
- get_employee_client_breakdown: Detailed client hours per employee
- get_employee_productivity_score: Productivity rating and performance category

DATA SOURCE: DDMac Analytics Supabase (separate from communication database)

OUTPUT: Provide clear text summaries with key metrics, percentages, and insights. Include employee names, hours worked, utilization rates, and performance categories."""

