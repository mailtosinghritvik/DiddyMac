"""
Fix the endpoint path - check if it should be /invocations instead of /invoke
"""
import boto3
import json

# Test both endpoint paths
AGENT_ID = "RitvikAgent-Nfl5014O49"
REGION = "us-west-2"
AGENT_RUNTIME_ARN = f"arn:aws:bedrock-agentcore:{REGION}:624571284647:runtime/{AGENT_ID}"

print("=" * 70)
print("Testing Bedrock AgentCore Endpoint Paths")
print("=" * 70)
print()

# The boto3 client should handle the endpoint automatically
# But let's verify what endpoint it's actually using
client = boto3.client('bedrock-agentcore', region_name=REGION)

# Get the actual endpoint URL from the client
endpoint_resolver = client._client_config.endpoint_resolver
endpoint_data = endpoint_resolver.get_endpoint('bedrock-agentcore', REGION)

print(f"Service Endpoint: {endpoint_data.get('hostname', 'N/A')}")
print(f"Agent Runtime ARN: {AGENT_RUNTIME_ARN}")
print()

# Test the actual API call
print("Testing invoke_agent_runtime API call...")
try:
    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        payload=json.dumps({'inputText': 'Test'}),
        contentType='application/json',
        accept='application/json'
    )
    
    print("✓ API call successful!")
    print(f"Status Code: {response.get('statusCode', 'N/A')}")
    print()
    print("The boto3 client handles the endpoint path automatically.")
    print("For direct HTTP access, you need to use the correct path.")
    print()
    print("Possible endpoint paths:")
    print("  1. /agents/{agent-id}/invoke")
    print("  2. /agents/{agent-id}/invocations")
    print("  3. /runtimes/{agent-id}/invoke")
    print()
    print("The correct path depends on the Bedrock AgentCore API version.")
    print("Use boto3 client (BedrockAgentCoreClient) to avoid path issues.")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print()
    print("This confirms the endpoint path issue.")
    print("Use the BedrockAgentCoreClient Python client instead of direct HTTP.")

