"""
Custom WhatsApp tool using Zapier webhook
Follows OpenAI Agents SDK custom tool pattern
"""
from agents import function_tool
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Zapier webhook URL for WhatsApp
ZAPIER_WEBHOOK_URL = os.getenv(
    "ZAPIER_WHATSAPP_WEBHOOK",
    "https://hooks.zapier.com/hooks/catch/your_webhook_id/"
)

@function_tool
async def send_whatsapp_via_zapier(phone_number: str, message: str) -> str:
    """
    Send a WhatsApp message via Zapier webhook.
    
    CRITICAL: Phone number MUST include + prefix and country code in international format.
    The WhatsApp API requires this format for delivery.
    
    Examples of CORRECT format:
    - +919932270002 (India)
    - +14165551234 (USA/Canada)
    - +447123456789 (UK)
    - +5511987654321 (Brazil)
    
    Examples of WRONG format (will be rejected):
    - 919932270002 (missing + prefix)
    - 14165551234 (missing + prefix)
    - 9932270002 (missing country code)
    
    Args:
        phone_number: Recipient phone number in international format with + prefix (required).
                     Must start with + followed by country code and number.
        message: Message content to send via WhatsApp. Keep concise for best mobile experience.
    
    Returns:
        Status message with delivery confirmation or error details
    """
    # Validate phone number format
    if not phone_number:
        return "❌ Error: Phone number is required"
    
    if not phone_number.startswith('+'):
        return f"❌ Error: Phone number must start with + for international format. Received: {phone_number}. Please provide with + prefix (e.g., +919932270002)"
    
    if len(phone_number) < 11:
        return f"❌ Error: Phone number too short (minimum 11 characters with country code). Received: {phone_number}"
    
    if not message:
        return "❌ Error: Message content is required"
    
    # Log attempt (for debugging)
    print(f"[WhatsApp Tool] Sending to {phone_number} via Zapier webhook...")
    print(f"[WhatsApp Tool] Message length: {len(message)} characters")
    
    # Prepare Zapier payload
    payload = {
        'phone_number': phone_number,
        'message': message
    }
    
    try:
        # Send POST request to Zapier webhook
        response = requests.post(
            ZAPIER_WEBHOOK_URL,
            json=payload,
            timeout=15,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"[WhatsApp Tool] Zapier response status: {response.status_code}")
        
        # Check response status
        if response.status_code == 200:
            try:
                # Try to parse JSON response
                response_data = response.json()
                
                if response_data.get('status') == 'success':
                    request_id = response_data.get('id', 'N/A')
                    print(f"[WhatsApp Tool] ✅ Success! Request ID: {request_id}")
                    return f"✅ WhatsApp message sent successfully to {phone_number}. Zapier request ID: {request_id}. The message has been delivered through the Zapier webhook."
                else:
                    print(f"[WhatsApp Tool] ⚠️ Unclear status: {response_data}")
                    return f"⚠️ Zapier webhook received the request but returned unclear status: {response_data}. The message may still be delivered."
            
            except ValueError:
                # Response is not JSON (Zapier might return plain text on success)
                response_text = response.text[:200]
                print(f"[WhatsApp Tool] ✅ Non-JSON response: {response_text}")
                return f"✅ WhatsApp message sent to {phone_number}. Zapier acknowledged request. Response: {response_text}"
        
        elif response.status_code == 202:
            # Accepted but processing async
            return f"✅ WhatsApp message accepted for delivery to {phone_number}. Zapier is processing asynchronously."
        
        else:
            # Error status code
            error_text = response.text[:200] if response.text else "No error message"
            print(f"[WhatsApp Tool] ❌ Failed with status {response.status_code}")
            return f"❌ Zapier webhook failed with status code {response.status_code}. Error: {error_text}"
    
    except requests.exceptions.Timeout:
        print(f"[WhatsApp Tool] ⏳ Request timed out")
        return f"⏳ Request to Zapier webhook timed out after 15 seconds. The message may still be processing in the background and could be delivered."
    
    except requests.exceptions.ConnectionError as e:
        print(f"[WhatsApp Tool] ❌ Connection error: {str(e)}")
        return f"❌ Could not connect to Zapier webhook. Please check internet connection and webhook URL. Error: {str(e)}"
    
    except Exception as e:
        print(f"[WhatsApp Tool] ❌ Unexpected error: {str(e)}")
        return f"❌ Unexpected error calling Zapier webhook: {str(e)}"

