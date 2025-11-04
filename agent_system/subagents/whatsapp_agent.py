from .base_subagent import BaseSubAgent
from agent_system.tools.whatsapp_zapier_tool import send_whatsapp_via_zapier

class WhatsAppAgent(BaseSubAgent):
    """
    Specialized agent for WhatsApp messaging via Zapier webhook
    Uses: Custom Zapier tool (not Composio)
    Configured with GPT-5-nano, minimal reasoning effort, low verbosity
    
    Primary use: Send task completion confirmations to WhatsApp numbers
    """
    
    def __init__(self, logger=None):
        super().__init__(
            name="WhatsApp Agent",
            toolkits=[],  # No Composio toolkits - using custom tool
            custom_tools=[send_whatsapp_via_zapier],  # Zapier webhook tool
            description="Send WhatsApp messages and confirmations via Zapier webhook integration",
            logger=logger,
            agent_type="whatsapp"
        )
        
        if logger:
            logger.log("WhatsApp Agent initialized with optimization profile")
            logger.log("Integration: Zapier webhook (custom function tool)")
            logger.log("Tool: send_whatsapp_via_zapier")
    
    def get_specialized_instructions(self) -> str:
        """
        Compressed WhatsApp-specific instructions
        """
        return """TOOL: send_whatsapp_via_zapier(phone_number: str, message: str)

PHONE FORMAT (CRITICAL):
- MUST include + prefix: +919932270002 (India), +14165551234 (USA)
- Use phone number EXACTLY as provided in task
- Tool validates and rejects without +

MESSAGE FORMATTING:
- Status emoji: ✅ (success), ⏳ (processing), ❌ (error)  
- Bold titles: *Task Completed*
- Concise: <800 chars ideal
- Bullet points for lists
- Include clickable links

STRUCTURE:
✅ *Task Completed*

[What was done - 2-3 lines]

Key details:
- Detail 1
- Detail 2

_Processed by AI agents_

OUTPUT: Phone (masked), message preview, status (sent/failed)."""

