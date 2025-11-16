"""Test the fixed endpoint"""
from utils.bedrock_agentcore_client import BedrockAgentCoreClient
import json

print("Testing fixed Bedrock AgentCore endpoint...")
print("=" * 70)

client = BedrockAgentCoreClient()
result = client.invoke('Hello, this is a test message')

if result.get('success'):
    print("✓ SUCCESS! Endpoint is working!")
    print()
    print("Response:")
    print(json.dumps(result.get('response', {}), indent=2, default=str))
else:
    print("✗ ERROR:")
    print(result.get('error'))
    print()
    print("Error details:")
    print(json.dumps(result, indent=2, default=str))

