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
        Enhanced report-specific instructions with Drive folder creation
        """
        return """DOCUMENT OPERATIONS:
- Create Google Docs with professional formatting
- Create Google Drive folders for organizing reports and resources
- Share documents/folders with "anyone with link can view" permissions
- Structure: Headings, bullets, tables, executive summaries

SHARING WORKFLOW:
1. Create Google Drive folder for the report/project
2. Create Google Doc(s) inside the folder
3. Upload any additional files (CSVs, charts) to the folder
4. Set folder permissions to "anyone with link can view"
5. Return folder link AND document link

DOCUMENT TYPES: Reports, proposals, meeting notes, documentation, analytics summaries

CRITICAL FOR REPORTS:
- Always create a dedicated folder for multi-file reports
- Set sharing to "anyone with the link can view"
- Include folder link in response for easy access
- Organize content logically (main doc + supporting files)

OUTPUT: Folder link, document ID/URL, sharing permissions set to "anyone with link", section breakdown, file count."""

