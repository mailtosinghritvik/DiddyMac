"""
Test Code Interpreter and Drive folder creation
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import process_request

def test_visualization_and_drive():
    """
    Test creating visualizations and Google Drive folder sharing
    """
    
    test_input = {
        "id": 1,
        "created_at": datetime.now().isoformat(),
        "user": "mailtosinghritvik@gmail.com",
        "source": "email",
        "input": "Create a chart showing the top 5 employees by hours worked, save it as a PNG, then create a Google Drive folder called 'Team Performance Report', put the chart in it, and share the folder link with me via email.",
        "subject": "Visualization Test"
    }
    
    print("\n" + "="*100)
    print("TESTING CODE INTERPRETER + GOOGLE DRIVE FOLDER CREATION")
    print("="*100)
    print(f"\nQuery: {test_input['input']}")
    print("\n" + "="*100)
    print("PROCESSING...")
    print("="*100 + "\n")
    
    result = process_request(test_input)
    
    print("\n" + "="*100)
    print("RESULT")
    print("="*100)
    print(f"\nStatus: {result.get('status')}")
    
    if result.get('final_output'):
        print(f"\nOutput:\n{result.get('final_output')}")
    
    if result.get('email_response_sent'):
        print(f"\n✅ Email sent to: {result.get('email_details', {}).get('recipient')}")
        print(f"   Subject: {result.get('email_details', {}).get('subject')}")
    
    print(f"\n📁 Logs: {result.get('output_dir')}")
    print("="*100 + "\n")
    
    return result

if __name__ == "__main__":
    result = test_visualization_and_drive()
    
    if result.get('status') == 'success':
        print("✅ Visualization test completed successfully")
    else:
        print(f"❌ Test failed: {result.get('error')}")

