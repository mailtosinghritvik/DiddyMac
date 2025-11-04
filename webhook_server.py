from flask import Flask, request, jsonify
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.supabase_client import SupabaseClient
from utils.logger import AgentLogger
from utils.whatsapp_helper import extract_phone_number, format_whatsapp_confirmation, mask_phone_number
from utils.message_utils import is_bot_message
from agent_system.memory_agent import MemoryAgent
from agent_system.orchestrator_agent import OrchestratorAgent
from agent_system.subagents.whatsapp_agent import WhatsAppAgent

app = Flask(__name__)

async def process_webhook_request_async(webhook_data: dict) -> dict:
    """
    Process incoming webhook request from Supabase (async)
    
    Args:
        webhook_data: Webhook payload containing record data
    
    Returns:
        Dictionary with processing results
    """
    # Extract record from webhook payload
    # Supabase webhook sends data in 'record' field for INSERT events
    record = webhook_data.get('record', webhook_data)
    
    # CRITICAL: Check if this is a bot-generated message (infinite loop prevention)
    input_text = record.get("input", "")
    if is_bot_message(input_text):
        # This is a bot confirmation message, skip processing to prevent infinite loop
        print(f"⏭️ SKIPPING BOT MESSAGE: {input_text[:100]}...")
        return {
            "status": "skipped",
            "reason": "bot_message_detected",
            "message": "Bot-generated confirmation skipped to prevent infinite loop",
            "record_id": record.get('id'),
            "detected_pattern": "Bot marker or multiple bot patterns found"
        }
    
    # Generate run_id for this execution
    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{record.get('source', 'unknown')}_{record.get('id', 'unknown')}"
    
    # Initialize logger
    logger = AgentLogger(run_id)
    logger.log("=== WEBHOOK REQUEST RECEIVED (DIDDYMAC) ===")
    logger.log(f"Webhook Data: {webhook_data}")
    logger.log(f"Record: {record}")
    logger.log("✅ Message validated: Not a bot confirmation (proceeding with processing)")
    
    # Save webhook payload
    logger.save_json("webhook_payload.json", webhook_data)
    logger.save_json("record.json", record)
    
    try:
        # Initialize Supabase client
        supabase = SupabaseClient()
        logger.log("Supabase client initialized")
        
        # Extract fields from record (already in database)
        user = record.get("user")
        source = record.get("source")
        input_text = record.get("input")
        subject = record.get("subject")
        created_at = record.get("created_at")
        record_id = record.get("id")
        
        logger.log(f"Processing record ID: {record_id}")
        logger.log(f"User: {user}, Source: {source}, Subject: {subject}")
        
        # Get message history
        logger.log("Fetching message history...")
        message_history = supabase.get_message_history(
            user=user,
            source=source,
            subject=subject,
            current_created_at=created_at
        )
        logger.log(f"Message history fetched")
        
        # Build input_body
        input_body = {
            "current_message_input": {
                "content": input_text,
                "timestamp": created_at,
                "sender": user,
                "source": source  # Added for WhatsApp detection
            },
            "phone_number": record.get("phone_number"),  # For WhatsApp confirmations
            "message_history": message_history
        }
        
        logger.save_json("input_body.json", input_body)
        
        # Initialize Memory Agent
        memory_agent = MemoryAgent(supabase, logger)
        
        # Process with Memory Agent (async)
        memory_output = await memory_agent.process_async(input_body)
        logger.save_json("memory_agent_output.json", memory_output)
        
        # Check if this is a rule creation request
        if memory_output.get("type") == "rule_creation":
            logger.log("=== RULE CREATION COMPLETED ===")
            logger.log(f"New rule created: {memory_output.get('rule')}")
            
            result = {
                "status": "success",
                "type": "rule_creation",
                "message": "Rule created successfully",
                "rule": memory_output.get("rule"),
                "output_dir": logger.get_output_dir()
            }
            
            logger.save_json("final_result.json", result)
            return result
        
        # If action execution, continue to Orchestrator Agent (Agents SDK + GPT-5)
        logger.log("Proceeding to Orchestrator Agent (Agents SDK, GPT-5, agents-as-tools pattern)...")
        orchestrator = OrchestratorAgent(logger)
        
        orchestration_result = await orchestrator.process_async(memory_output, input_body)
        logger.save_json("orchestrator_output.json", orchestration_result)
        
        # Check if source is WhatsApp - if so, send confirmation
        whatsapp_sent = False
        whatsapp_details = None
        
        if orchestration_result.get("success") and source.lower() == "whatsapp":
            logger.log("\n=== WHATSAPP CONFIRMATION ===")
            logger.log("Source is WhatsApp - sending confirmation message...")
            
            # Extract phone number from record or input_body
            phone_number = record.get("phone_number") or extract_phone_number(input_body)
            
            if phone_number:
                logger.log(f"Phone number extracted: {mask_phone_number(phone_number)}")
                logger.log(f"Phone number format verification: {phone_number[:3]}...{phone_number[-4:]} (has + prefix: {phone_number.startswith('+')})")
                
                try:
                    # Format confirmation message
                    confirmation_msg = format_whatsapp_confirmation(
                        final_summary=orchestration_result.get("final_summary", ""),
                        turns_used=orchestration_result.get("turns_used", 0),
                        status="success"
                    )
                    
                    logger.log(f"Formatted WhatsApp message ({len(confirmation_msg)} chars)")
                    logger.save_text("whatsapp_confirmation.txt", confirmation_msg)
                    
                    # Send via WhatsApp Agent
                    whatsapp_agent = WhatsAppAgent(logger)
                    whatsapp_task = f"""Send this WhatsApp confirmation message.

CRITICAL: Use the phone number EXACTLY as provided with the + prefix for international format.
Phone number (with + prefix): {phone_number}

Message to send:
{confirmation_msg}

IMPORTANT: The phone number {phone_number} already includes the + prefix and country code. Use it EXACTLY as shown."""
                    whatsapp_run_result = await whatsapp_agent.run(whatsapp_task, max_turns=10)
                    whatsapp_result = {
                        "success": True,
                        "result": str(whatsapp_run_result.final_output)
                    }
                    
                    if whatsapp_result.get("success"):
                        logger.log("✅ WhatsApp confirmation sent successfully")
                        whatsapp_sent = True
                        whatsapp_details = {
                            "phone_number": mask_phone_number(phone_number),
                            "message_length": len(confirmation_msg),
                            "status": "sent"
                        }
                    else:
                        logger.log(f"❌ WhatsApp send failed: {whatsapp_result.get('error')}", "ERROR")
                        whatsapp_details = {
                            "phone_number": mask_phone_number(phone_number),
                            "status": "failed",
                            "error": whatsapp_result.get("error")
                        }
                
                except Exception as e:
                    logger.log(f"Error sending WhatsApp confirmation: {str(e)}", "ERROR")
                    whatsapp_details = {
                        "status": "error",
                        "error": str(e)
                    }
            else:
                logger.log("⚠️ Could not extract phone number from WhatsApp message", "WARNING")
                whatsapp_details = {
                    "status": "skipped",
                    "reason": "no_phone_number"
                }
        
        # Final result
        logger.log("=== REQUEST PROCESSING COMPLETED ===")
        
        result = {
            "status": "success" if orchestration_result.get("success") else "error",
            "type": "action_execution",
            "orchestration_result": orchestration_result,
            "whatsapp_confirmation_sent": whatsapp_sent,
            "whatsapp_details": whatsapp_details,
            "output_dir": logger.get_output_dir()
        }
        
        logger.save_json("final_result.json", result)
        return result
    
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        logger.log(error_msg, "ERROR")
        
        result = {
            "status": "error",
            "error": str(e),
            "output_dir": logger.get_output_dir()
        }
        
        logger.save_json("final_result.json", result)
        return result

def process_webhook_request(webhook_data: dict) -> dict:
    """
    Synchronous wrapper for process_webhook_request_async
    
    Args:
        webhook_data: Webhook payload
    
    Returns:
        Processing results
    """
    import asyncio
    return asyncio.run(process_webhook_request_async(webhook_data))

@app.route('/', methods=['POST'])
def webhook_endpoint():
    """
    Main webhook endpoint to receive POST requests from Supabase
    """
    try:
        # Log the raw request
        print(f"=== INCOMING REQUEST (DIDDYMAC) ===")
        print(f"Headers: {dict(request.headers)}")
        print(f"Body: {request.get_data(as_text=True)}")
        
        # Get JSON data from request
        webhook_data = request.get_json()
        
        if not webhook_data:
            return jsonify({
                "status": "error",
                "message": "No JSON data received"
            }), 400
        
        # Process the webhook request
        result = process_webhook_request(webhook_data)
        
        return jsonify(result), 200
    
    except Exception as e:
        # Print full traceback
        import traceback
        error_trace = traceback.format_exc()
        print(f"=== ERROR ===")
        print(error_trace)
        
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": error_trace
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "service": "DiddyMac Communication Agent System",
        "timestamp": datetime.now().isoformat()
    }), 200

if __name__ == "__main__":
    print("=" * 80)
    print("DIDDYMAC WEBHOOK SERVER (AGENTS SDK + GPT-5)")
    print("=" * 80)
    print(f"Starting server...")
    print(f"Architecture: OpenAI Agents SDK with GPT-5 series")
    print(f"Pattern: Agents-as-tools orchestration")
    print(f"Agents: Calendar, Email, Report Writer, WhatsApp")
    print(f"Listening for webhooks from Supabase")
    print(f"Port: 8000")
    print(f"Health check: http://localhost:8000/health")
    print("=" * 80)
    
    # Run Flask app
    # Note: In production, use a proper WSGI server like gunicorn
    app.run(host='0.0.0.0', port=8000, debug=True)

