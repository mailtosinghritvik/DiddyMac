import os
import sys
import asyncio
from typing import Dict, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.supabase_client import SupabaseClient
from utils.logger import AgentLogger
from utils.whatsapp_helper import extract_phone_number, format_whatsapp_confirmation, mask_phone_number
from agent_system.memory_agent import MemoryAgent
from agent_system.orchestrator_agent import OrchestratorAgent
from agent_system.subagents.whatsapp_agent import WhatsAppAgent

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
    # Initialize logger
    logger = AgentLogger(run_id)
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
        source = json_input.get("source")
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
            
            # Check if source is WhatsApp - if so, send confirmation
            source = input_body["current_message_input"].get("source", "")
            whatsapp_sent = False
            whatsapp_details = None
            
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
            
            result = {
                "status": "success",
                "type": memory_output.get("type"),  # "action_execution" or "both"
                "final_output": orchestrator_result.get("final_summary"),
                "turns_used": orchestrator_result.get("turns_used", 0),
                "whatsapp_confirmation_sent": whatsapp_sent,
                "whatsapp_details": whatsapp_details,
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

