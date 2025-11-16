# Bedrock AgentCore Endpoint Guide

## Finding Your Agent Endpoint

Based on your configuration, your agent details are:
- **Agent ID**: `RitvikAgent-Nfl5014O49`
- **Agent ARN**: `arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49`
- **Region**: `us-west-2`
- **Account**: `624571284647`

## Method 1: Using AWS CLI

### Get Agent Details
```bash
aws bedrock-agentcore get-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2
```

### ⚠️ Important: No Direct HTTP Endpoint

**Bedrock AgentCore does NOT expose a simple HTTP endpoint**. 

Use the **Python client** instead:
```python
from utils.bedrock_agentcore_client import BedrockAgentCoreClient

client = BedrockAgentCoreClient()
result = client.invoke("Your message")
```

For HTTP/webhook access, deploy `webhook_proxy.py` as a proxy server.

## Method 2: Using AWS Console

1. Go to **AWS Bedrock Console** → **AgentCore**
2. Select your agent: **RitvikAgent**
3. Navigate to the **Runtime** tab
4. The endpoint URL will be displayed there

## Method 3: Programmatic Access (Python)

### Using boto3 to Get Agent Details
```python
import boto3

bedrock_agentcore = boto3.client('bedrock-agentcore', region_name='us-west-2')

# Get agent details
response = bedrock_agentcore.get_agent(agentId='RitvikAgent-Nfl5014O49')
print(f"Agent ARN: {response['agent']['agentArn']}")

# Construct endpoint
region = 'us-west-2'
agent_id = 'RitvikAgent-Nfl5014O49'
endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com/agents/{agent_id}/invoke"
print(f"Endpoint: {endpoint}")
```

## Invoking the Agent from Outside AWS

### Using AWS CLI
```bash
aws bedrock-agentcore invoke-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2 \
    --input '{"prompt": "Hello, how are you?"}'
```

### Using curl with AWS Signature
```bash
# First, get AWS credentials configured
aws configure

# Then use AWS CLI to sign the request
aws bedrock-agentcore invoke-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2 \
    --input '{"prompt": "Your message here"}' \
    --output json
```

### Using Python (boto3)
```python
import boto3
import json

bedrock_agentcore = boto3.client('bedrock-agentcore', region_name='us-west-2')

response = bedrock_agentcore.invoke_agent(
    agentId='RitvikAgent-Nfl5014O49',
    inputText='Hello, how are you?',
    sessionId='your-session-id'  # Optional: for maintaining conversation context
)

print(json.dumps(response, indent=2))
```

### Using HTTP Request (with AWS Signature)
For external applications, you'll need to sign requests using AWS Signature Version 4. Use libraries like:
- **Python**: `requests-aws4auth` or `botocore`
- **Node.js**: `aws4` or `@aws-sdk/signature-v4`
- **Java**: AWS SDK for Java

Example with Python:
```python
import requests
from requests_aws4auth import AWS4Auth
import boto3

# Get credentials
session = boto3.Session()
credentials = session.get_credentials()

# Create auth
auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    'us-west-2',
    'bedrock-agentcore',
    session_token=credentials.token
)

# Make request
url = 'https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke'
headers = {
    'Content-Type': 'application/json'
}
payload = {
    'inputText': 'Hello, how are you?',
    'sessionId': 'optional-session-id'
}

response = requests.post(url, json=payload, auth=auth, headers=headers)
print(response.json())
```

## Request Format

Your agent expects requests in this format (based on `agent.py`):

```json
{
  "prompt": "Your message here",
  "user": "user@example.com",
  "source": "email",
  "subject": "Optional subject",
  "phone_number": "Optional phone number"
}
```

Or the standard Bedrock AgentCore format:
```json
{
  "inputText": "Your message here",
  "sessionId": "optional-session-id-for-context"
}
```

## Authentication Requirements

1. **AWS Credentials**: You need valid AWS credentials with permissions to invoke the agent
2. **IAM Permissions**: Your IAM user/role needs:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "bedrock-agentcore:InvokeAgent",
       "bedrock-agentcore:GetAgent"
     ],
     "Resource": "arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49"
   }
   ```

## Testing the Endpoint

### Quick Test with AWS CLI
```bash
aws bedrock-agentcore invoke-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2 \
    --input '{"prompt": "Test message"}' \
    --output json > test_response.json
```

### Health Check
Your agent also exposes health check endpoints (when running):
- `GET /` - Health check
- `GET /ping` - Ping endpoint
- `GET /health` - Health status

## Important Notes

1. **Network Mode**: Your agent is configured with `network_mode: PUBLIC`, which means it's accessible from the internet
2. **Protocol**: Your agent uses `HTTP` protocol on port `8080` internally
3. **Session Management**: Use `sessionId` to maintain conversation context across multiple invocations
4. **Rate Limits**: Be aware of AWS service limits and quotas for Bedrock AgentCore

## Troubleshooting

### If you get "Access Denied":
- Check IAM permissions
- Verify AWS credentials are configured correctly
- Ensure the agent ID is correct

### If you get "Agent not found":
- Verify the agent ID: `RitvikAgent-Nfl5014O49`
- Check the region: `us-west-2`
- Ensure the agent is deployed and active

### If you get connection errors:
- Verify network connectivity
- Check if your firewall allows outbound HTTPS to AWS endpoints
- Ensure you're using the correct region endpoint

