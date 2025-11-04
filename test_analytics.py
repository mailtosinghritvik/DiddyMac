"""
Test script for DiddyMac Analytics Agents
Tests complex multi-part analytics queries with dual intent
"""
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import process_request

def test_complex_analytics_with_dual_intent():
    """
    Test complex analytics query with:
    1. Rule creation (client/project interchange)
    2. Multiple analytics questions in one message
    3. Email source (should get response via email)
    """
    
    test_input = {
        "id": 1,
        "created_at": datetime.now().isoformat(),
        "user": "mailtosinghritvik@gmail.com",
        "source": "email",
        "input": "Remember that I will use client and project interchangeably. Now find me the best performers of all time, find me the total time of Leeswood Danforth project, and give me a list of all the tasks in Shadow 2 client.",
        "subject": "Analytics Request"
    }
    
    print("\n" + "="*100)
    print("TESTING DIDDYMAC - COMPLEX ANALYTICS QUERY WITH DUAL INTENT")
    print("="*100)
    print(f"\nUser: {test_input['user']}")
    print(f"Source: {test_input['source']}")
    print(f"Query: {test_input['input']}")
    print("\n" + "="*100)
    print("PROCESSING...")
    print("="*100 + "\n")
    
    result = process_request(test_input)
    
    print("\n" + "="*100)
    print("FINAL RESULT")
    print("="*100)
    print(f"\nStatus: {result.get('status')}")
    print(f"Type: {result.get('type')}")
    
    if result.get('rule_created'):
        print(f"\n📋 RULE CREATED:")
        rule = result.get('rule_created')
        print(f"  - Instruction: {rule.get('rule_instruction')}")
        print(f"  - Category: {rule.get('rule_org')}")
        print(f"  - ID: {rule.get('id')}")
    
    if result.get('final_output'):
        print(f"\n⚡ ACTION OUTPUT:")
        print(result.get('final_output'))
    
    if result.get('error'):
        print(f"\n❌ ERROR:")
        print(result.get('error'))
    
    print(f"\n📁 Output Directory: {result.get('output_dir')}")
    print("\n" + "="*100)
    print("TEST COMPLETE")
    print("="*100 + "\n")
    
    return result

if __name__ == "__main__":
    result = test_complex_analytics_with_dual_intent()
    
    # Print summary
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100)
    
    if result.get('status') == 'success':
        print("✅ Test passed successfully")
        
        if result.get('type') == 'both':
            print("✅ Dual intent handled correctly (rule + action)")
        elif result.get('type') == 'action_execution':
            print("✅ Action executed successfully")
        elif result.get('type') == 'rule_creation':
            print("✅ Rule created successfully")
        
        if result.get('whatsapp_confirmation_sent'):
            print("✅ WhatsApp confirmation sent")
        
        print(f"\n📊 Turns used: {result.get('turns_used', 'N/A')}")
    else:
        print("❌ Test failed")
        print(f"Error: {result.get('error')}")
    
    print("="*100 + "\n")

