# API Call Examples for Bedrock AgentCore

## Quick Start

### Python - Using boto3 (Recommended - Easiest)

```python
import boto3

# Initialize client
client = boto3.client('bedrock-agentcore', region_name='us-west-2')

# Invoke agent
response = client.invoke_agent(
    agentId='RitvikAgent-Nfl5014O49',
    inputText='Hello, how are you?'
)

print(response)
```

### Python - Using the Client Utility

```python
from utils.bedrock_agentcore_client import BedrockAgentCoreClient, invoke_bedrock_agent

# Method 1: Using convenience function
result = invoke_bedrock_agent("Hello, how are you?")
print(result)

# Method 2: Using client class (more control)
client = BedrockAgentCoreClient(
    agent_id='RitvikAgent-Nfl5014O49',
    region='us-west-2'
)

result = client.invoke("Hello, how are you?")
print(result['response'])

# Method 3: Custom format (matches your agent.py)
result = client.invoke_custom_format(
    prompt="Schedule a meeting tomorrow at 3pm",
    user="user@example.com",
    source="email",
    subject="Meeting Request"
)
```

---

## Complete Examples

### Python Examples

#### Example 1: Basic Invocation
```python
import boto3
import json

# Create client
bedrock_client = boto3.client('bedrock-agentcore', region_name='us-west-2')

# Invoke agent
response = bedrock_client.invoke_agent(
    agentId='RitvikAgent-Nfl5014O49',
    inputText='Hello, how are you?'
)

# Process response
print(json.dumps(response, indent=2, default=str))
```

#### Example 2: With Session (Conversation Context)
```python
import boto3

bedrock_client = boto3.client('bedrock-agentcore', region_name='us-west-2')

# First message
response1 = bedrock_client.invoke_agent(
    agentId='RitvikAgent-Nfl5014O49',
    inputText='My name is John',
    sessionId='my-session-id-123'
)

# Get session ID from response (if not provided)
session_id = response1.get('sessionId', 'my-session-id-123')

# Follow-up message (maintains context)
response2 = bedrock_client.invoke_agent(
    agentId='RitvikAgent-Nfl5014O49',
    inputText='What is my name?',
    sessionId=session_id
)

print(response2)
```

#### Example 3: Using requests with AWS Signature
```python
import requests
from requests_aws4auth import AWS4Auth
import boto3

# Get AWS credentials
session = boto3.Session()
credentials = session.get_credentials()

# Create AWS signature auth
auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    'us-west-2',
    'bedrock-agentcore',
    session_token=credentials.token
)

# Make API call
url = 'https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke'
headers = {'Content-Type': 'application/json'}
payload = {
    'inputText': 'Hello, how are you?'
}

response = requests.post(url, json=payload, auth=auth, headers=headers)
print(response.json())
```

#### Example 4: Async/Await (for FastAPI/async apps)
```python
import boto3
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Create thread pool for boto3 (which is synchronous)
executor = ThreadPoolExecutor(max_workers=10)
bedrock_client = boto3.client('bedrock-agentcore', region_name='us-west-2')

async def invoke_agent_async(input_text: str, session_id: str = None):
    """Async wrapper for boto3 client"""
    loop = asyncio.get_event_loop()
    
    params = {
        'agentId': 'RitvikAgent-Nfl5014O49',
        'inputText': input_text
    }
    if session_id:
        params['sessionId'] = session_id
    
    response = await loop.run_in_executor(
        executor,
        lambda: bedrock_client.invoke_agent(**params)
    )
    return response

# Usage
async def main():
    result = await invoke_agent_async("Hello, how are you?")
    print(result)

# Run
asyncio.run(main())
```

#### Example 5: Error Handling
```python
import boto3
from botocore.exceptions import ClientError, BotoCoreError

bedrock_client = boto3.client('bedrock-agentcore', region_name='us-west-2')

try:
    response = bedrock_client.invoke_agent(
        agentId='RitvikAgent-Nfl5014O49',
        inputText='Hello, how are you?'
    )
    print("Success:", response)
    
except ClientError as e:
    error_code = e.response['Error']['Code']
    error_message = e.response['Error']['Message']
    print(f"AWS Error ({error_code}): {error_message}")
    
except BotoCoreError as e:
    print(f"BotoCore Error: {e}")
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

### JavaScript/Node.js Examples

#### Example 1: Using AWS SDK v3
```javascript
import { BedrockAgentCoreClient, InvokeAgentCommand } from "@aws-sdk/client-bedrock-agentcore";

const client = new BedrockAgentCoreClient({ region: "us-west-2" });

const command = new InvokeAgentCommand({
  agentId: "RitvikAgent-Nfl5014O49",
  inputText: "Hello, how are you?",
  sessionId: "optional-session-id"
});

try {
  const response = await client.send(command);
  console.log(response);
} catch (error) {
  console.error("Error:", error);
}
```

#### Example 2: Using AWS SDK v2
```javascript
const AWS = require('aws-sdk');

AWS.config.update({ region: 'us-west-2' });
const bedrockAgentCore = new AWS.BedrockAgentCore();

const params = {
  agentId: 'RitvikAgent-Nfl5014O49',
  inputText: 'Hello, how are you?'
};

bedrockAgentCore.invokeAgent(params, (err, data) => {
  if (err) {
    console.error("Error:", err);
  } else {
    console.log("Success:", data);
  }
});
```

#### Example 3: Using fetch with AWS Signature
```javascript
import { SignatureV4 } from "@aws-sdk/signature-v4";
import { Sha256 } from "@aws-crypto/sha256-js";
import { defaultProvider } from "@aws-sdk/credential-provider-node";

const signer = new SignatureV4({
  credentials: defaultProvider(),
  region: "us-west-2",
  service: "bedrock-agentcore",
  sha256: Sha256
});

const url = "https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke";
const request = {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    inputText: "Hello, how are you?"
  })
};

const signedRequest = await signer.sign(request);
const response = await fetch(url, signedRequest);
const data = await response.json();
console.log(data);
```

---

### cURL Example (Generated)

Use the script to generate a signed curl command:

```bash
python get_curl_command.py --input "Hello, how are you?"
```

This outputs a ready-to-use curl command with AWS signature.

---

## Integration Examples

### FastAPI Endpoint Example

```python
from fastapi import FastAPI, HTTPException
from utils.bedrock_agentcore_client import BedrockAgentCoreClient
import boto3

app = FastAPI()
bedrock_client = BedrockAgentCoreClient()

@app.post("/api/bedrock/invoke")
async def invoke_bedrock(request: dict):
    """API endpoint that calls Bedrock AgentCore"""
    try:
        input_text = request.get("input_text") or request.get("prompt")
        session_id = request.get("session_id")
        
        if not input_text:
            raise HTTPException(status_code=400, detail="input_text or prompt is required")
        
        result = bedrock_client.invoke(
            input_text=input_text,
            session_id=session_id
        )
        
        if result['success']:
            return result['response']
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Flask Endpoint Example

```python
from flask import Flask, request, jsonify
from utils.bedrock_agentcore_client import BedrockAgentCoreClient

app = Flask(__name__)
bedrock_client = BedrockAgentCoreClient()

@app.route('/api/bedrock/invoke', methods=['POST'])
def invoke_bedrock():
    """API endpoint that calls Bedrock AgentCore"""
    data = request.json
    input_text = data.get('input_text') or data.get('prompt')
    session_id = data.get('session_id')
    
    if not input_text:
        return jsonify({'error': 'input_text or prompt is required'}), 400
    
    result = bedrock_client.invoke(
        input_text=input_text,
        session_id=session_id
    )
    
    if result['success']:
        return jsonify(result['response'])
    else:
        return jsonify({'error': result.get('error')}), 500
```

---

## Request/Response Format

### Request Format

**Standard Format:**
```json
{
  "inputText": "Hello, how are you?",
  "sessionId": "optional-session-id"
}
```

**Custom Format (for your agent.py):**
```json
{
  "prompt": "Schedule a meeting tomorrow at 3pm",
  "user": "user@example.com",
  "source": "email",
  "subject": "Meeting Request",
  "phone_number": "+1234567890"
}
```

### Response Format

```json
{
  "completion": "Agent's response text...",
  "stopReason": "END_TURN",
  "sessionId": "session-id-if-provided",
  "trace": {
    "orchestrationTrace": {...}
  }
}
```

---

## Configuration

### Environment Variables

```bash
# AWS Credentials (if not using IAM roles)
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-west-2

# Or use AWS CLI
aws configure
```

### IAM Permissions Required

Your IAM user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgent",
        "bedrock-agentcore:GetAgent"
      ],
      "Resource": "arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49"
    }
  ]
}
```

---

## Testing

### Quick Test Script

```python
# test_bedrock_api.py
from utils.bedrock_agentcore_client import invoke_bedrock_agent

result = invoke_bedrock_agent("Hello, how are you?")
print(result)
```

Run:
```bash
python test_bedrock_api.py
```

---

## Troubleshooting

### Common Issues

1. **Access Denied**
   - Check IAM permissions
   - Verify AWS credentials
   - Ensure correct region

2. **Agent Not Found**
   - Verify agent ID: `RitvikAgent-Nfl5014O49`
   - Check agent is deployed
   - Ensure correct region

3. **Connection Timeout**
   - Check network connectivity
   - Verify endpoint URL
   - Check firewall settings

4. **Invalid Signature**
   - Regenerate credentials
   - Check system time is synchronized
   - Verify service name is `bedrock-agentcore`

