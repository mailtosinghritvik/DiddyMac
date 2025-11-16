"""
Quick test script for Bedrock AgentCore API
"""
import json
import sys
from utils.bedrock_agentcore_client import BedrockAgentCoreClient, invoke_bedrock_agent

def test_basic_invoke():
    """Test basic agent invocation"""
    print("=" * 60)
    print("Test 1: Basic Invocation")
    print("=" * 60)
    
    result = invoke_bedrock_agent("Hello, how are you?")
    print(json.dumps(result, indent=2, default=str))
    print()

def test_custom_format():
    """Test custom format invocation"""
    print("=" * 60)
    print("Test 2: Custom Format")
    print("=" * 60)
    
    client = BedrockAgentCoreClient()
    result = client.invoke_custom_format(
        prompt="Schedule a meeting tomorrow at 3pm",
        user="user@example.com",
        source="email",
        subject="Meeting Request"
    )
    print(json.dumps(result, indent=2, default=str))
    print()

def test_with_session():
    """Test with session ID"""
    print("=" * 60)
    print("Test 3: With Session ID")
    print("=" * 60)
    
    client = BedrockAgentCoreClient()
    session_id = "test-session-123"
    
    # First message
    result1 = client.invoke("My name is John", session_id=session_id)
    print("First message:")
    print(json.dumps(result1, indent=2, default=str))
    print()
    
    # Follow-up message
    result2 = client.invoke("What is my name?", session_id=session_id)
    print("Follow-up message:")
    print(json.dumps(result2, indent=2, default=str))
    print()

def main():
    """Run all tests"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "basic":
            test_basic_invoke()
        elif test_name == "custom":
            test_custom_format()
        elif test_name == "session":
            test_with_session()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: basic, custom, session")
    else:
        # Run all tests
        try:
            test_basic_invoke()
        except Exception as e:
            print(f"Error in basic test: {e}")
        
        try:
            test_custom_format()
        except Exception as e:
            print(f"Error in custom format test: {e}")
        
        try:
            test_with_session()
        except Exception as e:
            print(f"Error in session test: {e}")

if __name__ == '__main__':
    main()

