"""
Simple example: How to call Bedrock AgentCore as an API
"""
import boto3
import json

# Method 1: Using boto3 (EASIEST - Recommended)
def call_bedrock_simple():
    """Simplest way to call Bedrock AgentCore"""
    # Create client
    client = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    # Call the API
    response = client.invoke_agent(
        agentId='RitvikAgent-Nfl5014O49',
        inputText='Hello, how are you?'
    )
    
    # Print response
    print(json.dumps(response, indent=2, default=str))
    return response


# Method 2: Using the utility client (More features)
def call_bedrock_with_utility():
    """Using the BedrockAgentCoreClient utility"""
    from utils.bedrock_agentcore_client import BedrockAgentCoreClient
    
    # Create client
    client = BedrockAgentCoreClient(
        agent_id='RitvikAgent-Nfl5014O49',
        region='us-west-2'
    )
    
    # Call the API
    result = client.invoke("Hello, how are you?")
    
    # Check result
    if result['success']:
        print("Success!")
        print(json.dumps(result['response'], indent=2, default=str))
    else:
        print(f"Error: {result.get('error')}")
    
    return result


# Method 3: Convenience function (Quickest)
def call_bedrock_quick():
    """Quick one-liner approach"""
    from utils.bedrock_agentcore_client import invoke_bedrock_agent
    
    result = invoke_bedrock_agent("Hello, how are you?")
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == '__main__':
    print("=" * 60)
    print("Example: Calling Bedrock AgentCore API")
    print("=" * 60)
    print()
    
    print("Method 1: Using boto3 directly")
    print("-" * 60)
    try:
        call_bedrock_simple()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Method 2: Using utility client")
    print("-" * 60)
    try:
        call_bedrock_with_utility()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Method 3: Quick convenience function")
    print("-" * 60)
    try:
        call_bedrock_quick()
    except Exception as e:
        print(f"Error: {e}")

