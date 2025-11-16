# Correct Endpoint Information

## ⚠️ Important: Use Python Client, Not Direct HTTP

The Bedrock AgentCore API uses **boto3's `invoke_agent_runtime`** method, which handles the endpoint path automatically. 

**DO NOT** try to access it via direct HTTP with `/invoke` or `/invocations` paths - these may not work correctly.

## ✅ Correct Way to Use

### Python (Recommended)

```python
from utils.bedrock_agentcore_client import BedrockAgentCoreClient

client = BedrockAgentCoreClient()
result = client.invoke("Your message here")

if result['success']:
    print(result['response']['completion'])
```

### Using boto3 Directly

```python
import boto3
import json

client = boto3.client('bedrock-agentcore', region_name='us-west-2')

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49',
    payload=json.dumps({'inputText': 'Hello'}),
    contentType='application/json',
    accept='application/json'
)

# Parse response
payload = json.loads(response['response'].read().decode('utf-8'))
print(payload)
```

## ❌ Don't Use Direct HTTP

**These paths may not work:**
- `https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke`
- `https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invocations`

**Why?**
- Bedrock AgentCore uses a runtime API that requires specific parameters
- The HTTP endpoint path is handled internally by boto3
- Direct HTTP access requires complex request signing and correct path format

## Solution for Webhooks

If you need a webhook endpoint, use the **webhook proxy**:

1. Deploy `webhook_proxy.py` to a cloud service (Railway, Heroku, etc.)
2. Use the proxy URL as your webhook endpoint
3. The proxy handles AWS authentication and calls Bedrock AgentCore

See `WEBHOOK_ENDPOINT_GUIDE.md` for details.

## Test Your Setup

```bash
python test_fixed_endpoint.py
```

This uses the correct Python client and will work reliably.

