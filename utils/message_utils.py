"""
Message utility functions for bot detection and message formatting
"""
import re
from typing import Optional

# Bot marker constant - must be unique and detectable
BOT_MARKER = "[BOT_CONFIRMATION]"

def add_bot_marker(message: str) -> str:
    """
    Add bot marker to message to prevent infinite loop
    
    Args:
        message: Message content
    
    Returns:
        Message with bot marker appended
    """
    # Add marker at end of message (hidden in WhatsApp)
    return f"{message}\n\n{BOT_MARKER}"

def is_bot_message(message: str) -> bool:
    """
    Check if message is a bot-generated confirmation
    
    Args:
        message: Message to check
    
    Returns:
        True if message appears to be from bot
    """
    if not message:
        return False
    
    # Check for explicit bot marker
    if BOT_MARKER in message:
        return True
    
    # Check for multiple bot patterns (stronger detection)
    bot_patterns = [
        r'✅.*Task Completed',
        r'Processed in \d+ steps by AI agents',
        r'\[BOT_CONFIRMATION\]',
        r'_Processed.*AI agents_'
    ]
    
    matches = 0
    for pattern in bot_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            matches += 1
    
    # If 2+ patterns match, likely a bot message
    return matches >= 2

def extract_user_message(message: str) -> str:
    """
    Extract user message from a message that might contain bot marker
    
    Args:
        message: Message with potential bot marker
    
    Returns:
        User message without bot marker
    """
    if BOT_MARKER in message:
        return message.split(BOT_MARKER)[0].strip()
    return message.strip()

