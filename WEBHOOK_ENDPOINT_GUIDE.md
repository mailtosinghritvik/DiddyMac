# Webhook Endpoint Guide for Bedrock AgentCore

## ⚠️ Important: No Direct HTTP Endpoint

**Bedrock AgentCore does NOT have a simple HTTP endpoint** like `/agents/{id}/invoke`.

You **MUST** use:
1. **Python client** (BedrockAgentCoreClient) - ✅ Working
2. **Webhook proxy** - Deploy `webhook_proxy.py` for HTTP access

**DO NOT** try to use direct HTTP endpoints - they will show "Invalid API path" error.

**Agent Details:**
- **Agent ID**: `RitvikAgent-Nfl5014O49`
- **Region**: `us-west-2`
- **Account**: `624571284647`

---

## How to Get Your Endpoint

### Method 1: From Configuration File

Your endpoint is already in your `.bedrock_agentcore.yaml`:
- Agent ID: `RitvikAgent-Nfl5014O49`
- Region: `us-west-2`

Endpoint format: `https://bedrock-agentcore.{region}.amazonaws.com/agents/{agent-id}/invoke`

### Method 2: Using AWS CLI

```bash
# Get agent details
aws bedrock-agentcore get-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2

# Construct endpoint
echo "https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke"
```

### Method 3: Using Python Script

```bash
python get_bedrock_endpoint.py
```

### Method 4: AWS Console

1. Go to **AWS Bedrock Console** → **AgentCore**
2. Select your agent: **RitvikAgent**
3. Navigate to **Runtime** tab
4. Copy the **Invoke URL**

---

## Using as Webhook

### Important: AWS Authentication Required

⚠️ **Bedrock AgentCore requires AWS Signature V4 authentication**. This means:
- You **cannot** use it directly as a simple webhook URL
- You need to sign requests with AWS credentials
- Most webhook services don't support AWS signature out of the box

### Solution Options

#### Option 1: Create a Proxy Webhook (Recommended)

Create a simple API endpoint that:
1. Receives webhook requests (no auth needed)
2. Signs the request with AWS credentials
3. Forwards to Bedrock AgentCore

#### Option 2: Use AWS API Gateway

Set up API Gateway in front of Bedrock AgentCore to handle authentication.

#### Option 3: Use Services with AWS Integration

Some services support AWS authentication natively.

---

## Webhook Integration Examples

### Example 1: Zapier Webhook

Zapier doesn't support AWS Signature directly. Create a proxy:

**Python Proxy (Flask/FastAPI):**
```python
from flask import Flask, request, jsonify
import boto3
from botocore.exceptions import ClientError

app = Flask(__name__)

@app.route('/webhook/bedrock', methods=['POST'])
def bedrock_webhook():
    """Proxy webhook that forwards to Bedrock AgentCore"""
    try:
        # Get webhook payload
        webhook_data = request.json
        
        # Extract message
        input_text = webhook_data.get('message') or webhook_data.get('input') or str(webhook_data)
        
        # Call Bedrock AgentCore
        bedrock_client = boto3.client('bedrock-agentcore', region_name='us-west-2')
        response = bedrock_client.invoke_agent(
            agentId='RitvikAgent-Nfl5014O49',
            inputText=input_text
        )
        
        return jsonify({
            'success': True,
            'response': response.get('completion', '')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**Deploy this proxy** (e.g., on Heroku, Railway, or AWS Lambda) and use its URL as webhook.

### Example 2: Make.com (Integromat)

Make.com supports AWS authentication:

1. **HTTP Module** → **Make an HTTP Request**
2. **URL**: `https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke`
3. **Method**: POST
4. **Authentication**: AWS Signature V4
5. **Region**: `us-west-2`
6. **Service**: `bedrock-agentcore`
7. **Body**:
```json
{
  "inputText": "{{webhook.message}}"
}
```

### Example 3: n8n Webhook

n8n supports AWS Signature:

1. Create **Webhook** node (trigger)
2. Create **HTTP Request** node
3. Configure:
   - **URL**: `https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke`
   - **Authentication**: AWS
   - **Service**: `bedrock-agentcore`
   - **Region**: `us-west-2`
   - **Body**: `{"inputText": "{{$json.body.message}}"}`

### Example 4: AWS Lambda Proxy

Deploy a Lambda function that acts as webhook proxy:

```python
import json
import boto3

def lambda_handler(event, context):
    """Lambda function to proxy webhook to Bedrock AgentCore"""
    
    # Parse webhook payload
    body = json.loads(event.get('body', '{}'))
    input_text = body.get('message') or body.get('input') or 'Hello'
    
    # Call Bedrock AgentCore
    bedrock_client = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    try:
        response = bedrock_client.invoke_agent(
            agentId='RitvikAgent-Nfl5014O49',
            inputText=input_text
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'response': response.get('completion', '')
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
```

**API Gateway URL** (from Lambda): Use this as your webhook URL.

---

## Request Format for Webhook

### Standard Format

```json
{
  "inputText": "Your message here",
  "sessionId": "optional-session-id"
}
```

### Custom Format (for your agent.py)

```json
{
  "prompt": "Your message here",
  "user": "user@example.com",
  "source": "webhook",
  "subject": "Optional subject"
}
```

---

## Webhook Services Comparison

| Service | AWS Auth Support | Setup Difficulty | Cost |
|---------|------------------|------------------|------|
| **Zapier** | ❌ No | Easy (with proxy) | Paid |
| **Make.com** | ✅ Yes | Medium | Paid |
| **n8n** | ✅ Yes | Medium | Free/Paid |
| **AWS API Gateway** | ✅ Yes | Medium | Pay per use |
| **Lambda Proxy** | ✅ Yes | Medium | Pay per use |
| **Custom Proxy** | ✅ Yes | Hard | Varies |

---

## Quick Setup: Simple Proxy Server

I'll create a simple proxy server you can deploy:

### Option A: Deploy on Railway/Heroku

```python
# webhook_proxy.py
from flask import Flask, request, jsonify
import boto3
import os

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    bedrock_client = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    data = request.json or {}
    input_text = data.get('message') or data.get('input') or str(data)
    
    response = bedrock_client.invoke_agent(
        agentId='RitvikAgent-Nfl5014O49',
        inputText=input_text
    )
    
    return jsonify({
        'success': True,
        'response': response.get('completion', '')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
```

Deploy this and use its URL as webhook (no AWS auth needed from webhook service).

---

## Testing Your Webhook

### Using curl

```bash
# Test webhook endpoint
curl -X POST https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke \
  -H "Content-Type: application/json" \
  -d '{"inputText": "Hello from webhook"}' \
  --aws-sigv4 "aws:amz:us-west-2:bedrock-agentcore"
```

### Using Postman

Import the collection: `Bedrock_AgentCore.postman_collection.json`

---

## Security Considerations

1. **AWS Credentials**: Never expose AWS credentials in webhook payloads
2. **Rate Limiting**: Implement rate limiting on proxy endpoints
3. **Validation**: Validate webhook payloads before forwarding
4. **Logging**: Log all webhook requests for debugging
5. **Error Handling**: Handle errors gracefully

---

## Summary

**Your Endpoint:**
```
https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke
```

**To Use as Webhook:**
1. ✅ **Make.com/n8n**: Use directly with AWS auth
2. ✅ **Zapier/Others**: Create a proxy server
3. ✅ **AWS Lambda**: Deploy Lambda function with API Gateway

**Quick Test:**
```bash
python get_bedrock_endpoint.py
```

---

## Next Steps

1. Choose your webhook service
2. Set up authentication (proxy or native)
3. Configure webhook URL
4. Test with a sample request
5. Monitor logs in CloudWatch

