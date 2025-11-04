from .base_subagent import BaseSubAgent

class CalendarAgent(BaseSubAgent):
    """
    Specialized agent for calendar and meeting management
    Uses: GOOGLECALENDAR, GOOGLEMEETS toolkits
    Configured with GPT-5-mini, low reasoning effort, low verbosity
    """
    
    def __init__(self, logger=None):
        super().__init__(
            name="Calendar Agent",
            toolkits=["GOOGLECALENDAR", "GOOGLEMEETS"],
            description="Specialized agent for scheduling meetings, creating calendar events, and managing Google Calendar with Google Meet integration",
            logger=logger,
            agent_type="calendar"
        )
        
        if logger:
            logger.log("Calendar Agent initialized with optimization profile")
            logger.log("Tools: Google Calendar, Google Meet")
    
    def get_specialized_instructions(self) -> str:
        """
        Compressed calendar-specific instructions
        """
        return """CALENDAR OPERATIONS:
- Schedule meetings with titles, descriptions, attendees
- Create Google Meet links for virtual meetings
- Duration: 30min (quick sync) or 60min (detailed meetings)
- Add reminders (default: 10 minutes before)

TIME HANDLING:
- Interpret relative times (tomorrow, next week)
- Business hours: 9 AM - 5 PM, prefer afternoons
- Consider time zones if mentioned

OUTPUT: Meeting title/time, attendees, Meet link, event ID, notes."""

