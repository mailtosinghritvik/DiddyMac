"""
WhatsApp helper functions for phone number extraction and message formatting
"""
import re
from typing import Dict, Any, Optional

def extract_phone_number(input_body: Dict[str, Any]) -> Optional[str]:
    """
    Extract phone number from input body
    
    Args:
        input_body: Input body containing current_message_input and other data
    
    Returns:
        Phone number string or None if not found
    """
    # Check various locations for phone number
    current_message = input_body.get("current_message_input", {})
    
    # Try sender field first
    sender = current_message.get("sender")
    if sender and is_phone_number(sender):
        return normalize_phone_number(sender)
    
    # Try phone_number field
    phone = input_body.get("phone_number") or current_message.get("phone_number")
    if phone:
        return normalize_phone_number(phone)
    
    # Try user field
    user = input_body.get("user") or current_message.get("user")
    if user and is_phone_number(user):
        return normalize_phone_number(user)
    
    return None

def is_phone_number(text: str) -> bool:
    """
    Check if text looks like a phone number
    
    Args:
        text: Text to check
    
    Returns:
        True if looks like phone number
    """
    if not text:
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', text)
    
    # Check if it's mostly digits with optional + prefix
    phone_pattern = r'^\+?\d{10,15}$'
    return bool(re.match(phone_pattern, cleaned))

def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to WhatsApp international format with + prefix
    
    Args:
        phone: Phone number in any format
    
    Returns:
        Normalized phone number with + and country code (e.g., +919932270002, +14165551234)
    """
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d\+]', '', phone)
    
    # Ensure it starts with + for international format
    if not cleaned.startswith('+'):
        # If number starts with country code digits but no +, add it
        if len(cleaned) >= 10:
            # Check if it starts with common country codes
            if cleaned.startswith('91') and len(cleaned) >= 12:  # India
                cleaned = '+' + cleaned
            elif cleaned.startswith('1') and len(cleaned) == 11:  # USA/Canada
                cleaned = '+' + cleaned
            else:
                # Default: assume US/Canada if 10 digits, otherwise add +
                if len(cleaned) == 10:
                    cleaned = '+1' + cleaned
                else:
                    cleaned = '+' + cleaned
        else:
            # Short number, assume US/Canada
            cleaned = '+1' + cleaned
    
    return cleaned

def format_whatsapp_confirmation(
    final_summary: str,
    turns_used: int = 0,
    status: str = "success"
) -> str:
    """
    Format orchestrator output into concise WhatsApp message with bot marker
    
    Args:
        final_summary: Full orchestrator output
        turns_used: Number of turns used
        status: success/error/processing
    
    Returns:
        WhatsApp-formatted message (concise) with bot marker for loop prevention
    """
    from utils.message_utils import add_bot_marker
    
    # Status emoji
    status_emoji = {
        "success": "✅",
        "error": "❌",
        "processing": "⏳"
    }.get(status, "ℹ️")
    
    # Truncate summary if too long
    max_length = 800  # WhatsApp comfort zone
    
    if len(final_summary) > max_length:
        # Try to find a good break point
        summary = final_summary[:max_length]
        last_period = summary.rfind('.')
        last_newline = summary.rfind('\n')
        
        break_point = max(last_period, last_newline)
        if break_point > max_length - 200:  # If break point is reasonable
            summary = final_summary[:break_point + 1]
        else:
            summary = final_summary[:max_length] + "..."
    else:
        summary = final_summary
    
    # Build message
    message = f"{status_emoji} *Task Completed*\n\n{summary}"
    
    # Add processing info if provided
    if turns_used > 0:
        message += f"\n\n_Processed in {turns_used} steps by AI agents_"
    
    # CRITICAL: Add bot marker to prevent infinite loop
    message = add_bot_marker(message)
    
    return message

def mask_phone_number(phone: str) -> str:
    """
    Mask phone number for privacy in logs
    
    Args:
        phone: Phone number to mask
    
    Returns:
        Masked phone number (+1234***7890)
    """
    if len(phone) > 7:
        return phone[:5] + "***" + phone[-4:]
    return "***" + phone[-4:] if len(phone) >= 4 else "***"

