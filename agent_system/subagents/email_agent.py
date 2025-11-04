from .base_subagent import BaseSubAgent

class EmailAgent(BaseSubAgent):
    """
    Specialized agent for email operations
    Uses: GMAIL, GOOGLEDOCS toolkits
    Configured with GPT-5, medium reasoning effort, medium verbosity
    """
    
    def __init__(self, logger=None):
        super().__init__(
            name="Email Agent",
            toolkits=["GMAIL", "GOOGLEDOCS"],
            description="Specialized agent for sending emails, reading inbox, drafting messages, managing Gmail communications, and referencing/attaching Google Docs",
            logger=logger,
            agent_type="email"
        )
        
        if logger:
            logger.log("Email Agent initialized with optimization profile")
            logger.log("Tools: Gmail, Google Docs")
    
    def get_specialized_instructions(self) -> str:
        """
        Compressed email-specific instructions
        """
        return """EMAIL OPERATIONS:
- Send/draft emails with proper formatting
- Include To/CC/BCC recipients
- Reference and share Google Docs (attach links, set permissions)

COMPOSITION:
- Clear subject lines
- Professional greeting/closing
- Well-structured body
- Tone: Formal (external), Professional (internal), Friendly (casual)

OUTPUT: Subject, recipients (To/CC/BCC), key points, status (sent/drafted), message ID, doc links if any."""

