from .base_subagent import BaseSubAgent

class ReportWriterAgent(BaseSubAgent):
    """
    Specialized agent for creating reports and documents
    Uses: GOOGLEDOCS toolkit
    Configured with GPT-5, medium reasoning effort, medium verbosity
    """
    
    def __init__(self, logger=None):
        super().__init__(
            name="Report Writer Agent",
            toolkits=["GOOGLEDOCS"],
            description="Specialized agent for creating structured reports, documents, and written content in Google Docs with professional formatting",
            logger=logger,
            agent_type="report_writer"
        )
        
        if logger:
            logger.log("Report Writer Agent initialized with optimization profile")
            logger.log("Tools: Google Docs")
    
    def get_specialized_instructions(self) -> str:
        """
        Compressed report-specific instructions
        """
        return """DOCUMENT OPERATIONS:
- Create Google Docs with professional formatting
- Structure: Headings, bullets, tables, executive summaries
- Set sharing permissions appropriately

DOCUMENT TYPES: Reports, proposals, meeting notes, documentation

OUTPUT: Document ID/URL, sharing permissions, section breakdown, word count."""

