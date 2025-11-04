"""
Message utility functions for bot detection and message formatting
"""
import re
from typing import Optional

# Unique bot marker to identify system-generated messages
BOT_MARKER = "🤖_AI_AGENT_"

# Pattern indicators that suggest bot-generated content
BOT_PATTERNS = [
    "✅ *Task Completed*",
    "_Processed in",
    "by AI agents_",
    "Zapier request ID:",
    "Message ID: 19a",
    "Event ID:",
    "Google Meet: https://meet.google.com",
    "Meeting created",
    "Email sent",
]

def is_bot_message(message: str) -> bool:
    """
    Check if message is from the bot system (to prevent infinite loops)
    
    Uses two layers of detection:
    1. Primary: Check for unique bot marker
    2. Backup: Check for multiple bot-specific patterns
    
    Args:
        message: Message content to check
    
    Returns:
        True if message is identified as bot-generated
    """
    if not message:
        return False
    
    # Layer 1: Check for the unique bot marker (most reliable)
    if BOT_MARKER in message:
        return True
    
    # Layer 2: Backup detection using pattern matching
    # If message has 2+ bot patterns, it's very likely a bot message
    pattern_matches = sum(1 for pattern in BOT_PATTERNS if pattern in message)
    if pattern_matches >= 2:
        return True
    
    return False

def add_bot_marker(message: str) -> str:
    """
    Add bot marker to message to enable detection
    
    Call this function before sending any bot-generated message
    to ensure it won't be processed as a new user request.
    
    Args:
        message: Original message content
    
    Returns:
        Message with bot marker appended (at the end, subtle)
    """
    # Add marker at the end of message
    # The marker is subtle and won't disrupt the user experience
    return f"{message}\n\n{BOT_MARKER}"

def remove_bot_marker(message: str) -> str:
    """
    Remove bot marker from message (if present)
    
    Args:
        message: Message that may contain bot marker
    
    Returns:
        Message with bot marker removed
    """
    return message.replace(BOT_MARKER, "").strip()

