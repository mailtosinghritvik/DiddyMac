import os
import sys
import asyncio
import hashlib
import uuid
from typing import Dict, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.supabase_client import SupabaseClient
from utils.logger import AgentLogger
from utils.whatsapp_helper import extract_phone_number, format_whatsapp_confirmation, mask_phone_number
from agent_system.memory_agent import MemoryAgent
from agent_system.orchestrator_agent import OrchestratorAgent
from agent_system.subagents.whatsapp_agent import WhatsAppAgent

# Request deduplication cache
# Stores hashes of recently processed requests to prevent duplicate processing
_processed_requests: Dict[str, datetime] = {}
_request_lock = asyncio.Lock()
DEDUP_WINDOW_SECONDS = 300  # 5 minutes

def _generate_request_hash(json_input: Dict[str, Any]) -> str:
    """
    Generate a unique hash for a request based on user, input, and timestamp
    Used for deduplication
    """
    # Create a deterministic hash from key fields
    key_fields = {
        "user": json_input.get("user", ""),
        "input": json_input.get("input", ""),
        "source": json_input.get("source", ""),
        "subject": json_input.get("subject", ""),
        # Round timestamp to nearest 10 seconds to catch near-simultaneous duplicates
        "timestamp": str(json_input.get("created_at", ""))[:16] if json_input.get("created_at") else ""
    }
    hash_str = hashlib.md5(str(sorted(key_fields.items())).encode()).hexdigest()
    return hash_str

async def _cleanup_old_requests():
    """Remove expired entries from the deduplication cache"""
    async with _request_lock:
        cutoff_time = datetime.now() - timedelta(seconds=DEDUP_WINDOW_SECONDS)
        expired_keys = [k for k, v in _processed_requests.items() if v < cutoff_time]
        for key in expired_keys:
            del _processed_requests[key]

async def process_request_async(json_input: Dict[str, Any], run_id: str = None) -> Dict[str, Any]:
    """
    Main async orchestrator function to process incoming requests through the agent pipeline
    Uses OpenAI Agents SDK with GPT-5 series models
    
    Args:
        json_input: Dictionary containing id, created_at, user, source, input, subject
        run_id: Optional run identifier for logging
    
    Returns:
        Dictionary with processing results
    """
    # Generate unique request ID for tracking
    request_uuid = str(uuid.uuid4())[:8]
    
    # Generate request hash for deduplication
    request_hash = _generate_request_hash(json_input)
    
    # Check if this request has been processed recently (deduplication)
    async with _request_lock:
        if request_hash in _processed_requests:
            time_since = (datetime.now() - _processed_requests[request_hash]).total_seconds()
            print(f"⚠️  DUPLICATE REQUEST DETECTED (ID: {request_uuid}, Hash: {request_hash[:8]})")
            print(f"   Request was processed {time_since:.1f} seconds ago - SKIPPING to prevent duplicate execution")
            return {
                "status": "skipped",
                "reason": "duplicate_request",
                "message": f"Request already processed {time_since:.1f} seconds ago",
                "request_id": request_uuid,
                "request_hash": request_hash[:8],
                "original_processing_time": _processed_requests[request_hash].isoformat()
            }
        
        # Mark this request as being processed
        _processed_requests[request_hash] = datetime.now()
    
    # Clean up old entries periodically (async task, non-blocking)
    asyncio.create_task(_cleanup_old_requests())
    
    # Initialize logger
    logger = AgentLogger(run_id)
    logger.log(f"🔵 REQUEST ID: {request_uuid} | Hash: {request_hash[:8]}")
    logger.log("=== STARTING REQUEST PROCESSING (DIDDYMAC - AGENTS SDK + GPT-5) ===")
    logger.log(f"Input: {json_input}")
    
    # Save original input
    logger.save_json("input.json", json_input)
    
    try:
        # Initialize Supabase client
        supabase = SupabaseClient()
        logger.log("Supabase client initialized")
        
        # Extract fields from input
        user = json_input.get("user")
        source = 'email'
        input_text = json_input.get("input")
        subject = json_input.get("subject")
        
        # Insert into input_db
        logger.log("Inserting input into database...")
        inserted_record = supabase.insert_input(user, source, input_text, subject)
        logger.log(f"Input stored with ID: {inserted_record.get('id')}")
        
        # Get message history
        logger.log("Fetching message history...")
        message_history = supabase.get_message_history(
            user=user,
            source=source,
            subject=subject,
            current_created_at=inserted_record.get("created_at")
        )
        logger.log(f"Message history fetched")
        
        # Build input_body
        input_body = {
            "current_message_input": {
                "content": input_text,
                "timestamp": inserted_record.get("created_at"),
                "sender": user,
                "source": source  # Added for WhatsApp detection
            },
            "phone_number": json_input.get("phone_number"),  # For WhatsApp confirmations
            "message_history": message_history
        }
        
        logger.save_json("input_body.json", input_body)
        
        # PHASE 1: MEMORY AGENT (GPT-5-mini with structured outputs)
        logger.log("\n=== PHASE 1: MEMORY AGENT ===")
        logger.log("Processing with Memory Agent (GPT-5-mini, minimal/low reasoning)...")
        
        memory_agent = MemoryAgent(supabase, logger)
        memory_output = await memory_agent.process_async(input_body)
        logger.save_json("memory_agent_output.json", memory_output)
        
        # Check if this is a rule-only request (no action)
        if memory_output.get("type") == "rule_creation":
            logger.log("=== RULE CREATION COMPLETED (No Action) ===")
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
        
        # PHASE 2: ORCHESTRATOR AGENT (GPT-5 with agents-as-tools)
        # Handles both action_execution and dual intent ("both")
        logger.log("\n=== PHASE 2: ORCHESTRATOR AGENT ===")
        
        # Check if this is dual intent (rule + action)
        is_dual_intent = memory_output.get("type") == "both"
        if is_dual_intent:
            logger.log("=== DUAL INTENT: Rule created, now executing action ===")
            logger.log(f"Rule created: {memory_output.get('rule_created', {}).get('rule_instruction')}")
        
        logger.log("Processing with Orchestrator Agent (GPT-5, dynamic reasoning, agents-as-tools pattern)...")
        
        orchestrator = OrchestratorAgent(logger)
        orchestrator_result = await orchestrator.process_async(memory_output, input_body)
        
        logger.save_json("orchestrator_output.json", orchestrator_result)
        
        if orchestrator_result.get("success"):
            logger.log("=== REQUEST PROCESSING COMPLETED SUCCESSFULLY ===")
            
            # Check source and send response via appropriate channel
            source = input_body["current_message_input"].get("source", "")
            whatsapp_sent = False
            whatsapp_details = None
            email_sent = False
            email_details = None
            
            if source.lower() == "whatsapp":
                logger.log("\n=== WHATSAPP CONFIRMATION ===")
                logger.log("Source is WhatsApp - sending confirmation message...")
                
                # Extract phone number
                phone_number = extract_phone_number(input_body)
                
                if phone_number:
                    logger.log(f"Phone number extracted: {mask_phone_number(phone_number)}")
                    logger.log(f"Phone number format verification: {phone_number[:3]}...{phone_number[-4:]} (has + prefix: {phone_number.startswith('+')})")
                    
                    try:
                        # Format confirmation message
                        confirmation_msg = format_whatsapp_confirmation(
                            final_summary=orchestrator_result.get("final_summary", ""),
                            turns_used=orchestrator_result.get("turns_used", 0),
                            status="success"
                        )
                        
                        logger.log(f"Formatted WhatsApp message ({len(confirmation_msg)} chars)")
                        logger.save_text("whatsapp_confirmation.txt", confirmation_msg)
                        
                        # Send via WhatsApp Agent
                        whatsapp_agent = WhatsAppAgent(logger)
                        
                        # Build explicit task for WhatsApp agent with phone format emphasis
                        whatsapp_task = f"""Send this WhatsApp confirmation message.

CRITICAL: Use the phone number EXACTLY as provided with the + prefix for international format.
Phone number (with + prefix): {phone_number}

Message to send:
{confirmation_msg}

IMPORTANT: The phone number {phone_number} already includes the + prefix and country code. Use it EXACTLY as shown."""
                        
                        # Use async run method with increased turns
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
            
            elif source.lower() == "email":
                logger.log("\n=== EMAIL RESPONSE ===")
                logger.log("Source is Email - sending response via email...")
                
                # Extract email address from user field
                recipient_email = input_body["current_message_input"].get("sender")
                
                if recipient_email and "@" in recipient_email:
                    logger.log(f"Recipient email: {recipient_email}")
                    
                    try:
                        # Import Email Agent
                        from agent_system.subagents.email_agent import EmailAgent
                        
                        # Format email response
                        subject = json_input.get("subject", "Re: Your Request")
                        if not subject.startswith("Re:"):
                            subject = f"Re: {subject}"
                        
                        email_body = f"""Hello,

Here are the results of your request:

{orchestrator_result.get("final_summary", "")}

---
This is an automated response from DiddyMac AI Agent System.
"""
                        
                        logger.log(f"Formatted email response for subject: {subject}")
                        logger.save_text("email_response.txt", email_body)
                        
                        # Send via Email Agent
                        email_agent = EmailAgent(logger)
                        
                        email_task = f"""Send this email response.

To: {recipient_email}
Subject: {subject}

Message:
{email_body}

Send the email now."""
                        
                        # Use async run method
                        email_run_result = await email_agent.run(email_task, max_turns=10)
                        email_result = {
                            "success": True,
                            "result": str(email_run_result.final_output)
                        }
                        
                        if email_result.get("success"):
                            logger.log("✅ Email response sent successfully")
                            email_sent = True
                            email_details = {
                                "recipient": recipient_email,
                                "subject": subject,
                                "status": "sent"
                            }
                        else:
                            logger.log(f"❌ Email send failed: {email_result.get('error')}", "ERROR")
                            email_details = {
                                "recipient": recipient_email,
                                "status": "failed",
                                "error": email_result.get("error")
                            }
                    
                    except Exception as e:
                        logger.log(f"Error sending email response: {str(e)}", "ERROR")
                        email_details = {
                            "status": "error",
                            "error": str(e)
                        }
                else:
                    logger.log("⚠️ Could not extract email address from user field", "WARNING")
                    email_details = {
                        "status": "skipped",
                        "reason": "no_email_address"
                    }
            
            result = {
                "status": "success",
                "type": memory_output.get("type"),  # "action_execution" or "both"
                "final_output": orchestrator_result.get("final_summary"),
                "turns_used": orchestrator_result.get("turns_used", 0),
                "whatsapp_confirmation_sent": whatsapp_sent,
                "whatsapp_details": whatsapp_details,
                "email_response_sent": email_sent,
                "email_details": email_details,
                "output_dir": logger.get_output_dir()
            }
            
            # Add rule creation info if dual intent
            if is_dual_intent and memory_output.get("rule_created"):
                result["rule_created"] = memory_output.get("rule_created")
                result["message"] = "Rule created and action executed successfully"
                logger.log(f"📋 Dual intent result: Rule ID {memory_output['rule_created'].get('id')} + Action completed")
            
            logger.save_json("final_result.json", result)
            return result
        else:
            logger.log("=== ORCHESTRATION FAILED ===", "ERROR")
            
            result = {
                "status": "error",
                "type": "action_execution",
                "error": orchestrator_result.get("error"),
                "message": orchestrator_result.get("message"),
                "output_dir": logger.get_output_dir()
            }
            
            logger.save_json("final_result.json", result)
            return result
    
    except Exception as e:
        error_msg = f"Error in main orchestrator: {str(e)}"
        logger.log(error_msg, "ERROR")
        logger.log(f"Exception details: {type(e).__name__}", "ERROR")
        
        import traceback
        logger.log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
        
        result = {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "output_dir": logger.get_output_dir()
        }
        
        logger.save_json("final_result.json", result)
        return result

def process_request(json_input: Dict[str, Any], run_id: str = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for process_request_async
    
    Args:
        json_input: Dictionary containing id, created_at, user, source, input, subject
        run_id: Optional run identifier for logging
    
    Returns:
        Dictionary with processing results
    """
    return asyncio.run(process_request_async(json_input, run_id))

if __name__ == "__main__":
    # Example usage
    test_input = {
        "id": 1,
        "created_at": datetime.now().isoformat(),
        "user": "test_user@example.com",
        "source": "email",
        "input": "Send an email to john@example.com about the project update and schedule a meeting for next Monday at 3pm",
        "subject": "Project Update"
    }
    
    print("\n" + "="*80)
    print("TESTING DIDDYMAC - GPT-5 AGENTS SDK IMPLEMENTATION")
    print("="*80 + "\n")
    
    result = process_request(test_input)
    
    print("\n" + "="*80)
    print("FINAL RESULT:")
    print("="*80)
    print(f"Status: {result.get('status')}")
    print(f"Type: {result.get('type')}")
    if result.get('final_output'):
        print(f"\nFinal Output:\n{result.get('final_output')}")
    if result.get('error'):
        print(f"\nError: {result.get('error')}")
    print(f"\nOutput Directory: {result.get('output_dir')}")
    print("="*80 + "\n")

