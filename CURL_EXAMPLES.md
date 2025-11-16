# Curl Examples for Bedrock AgentCore

## Quick Reference

**Endpoint:**
```
https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke
```

**Agent ID:** `RitvikAgent-Nfl5014O49`  
**Region:** `us-west-2`

---

## Method 1: Using AWS CLI (Easiest - Recommended)

The simplest way is to use AWS CLI, which handles authentication automatically:

```bash
aws bedrock-agentcore invoke-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2 \
    --input '{"inputText": "Hello, how are you?"}'
```

**With session ID (for conversation context):**
```bash
aws bedrock-agentcore invoke-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2 \
    --input '{"inputText": "Hello", "sessionId": "your-session-id"}' \
    --output json
```

---

## Method 2: Generate Signed Curl Command (Python Script)

I've created a script that generates a properly signed curl command:

```bash
# Generate a signed curl command
python generate_signed_curl.py --input "Hello, how are you?"

# With session ID
python generate_signed_curl.py --input "Hello" --session-id "your-session-id"

# Save to file
python generate_signed_curl.py --input "Hello" --save curl_command.sh
```

This will output a complete curl command with all AWS Signature V4 headers.

---

## Method 3: Using awscurl (Third-party tool)

Install `awscurl` first:
```bash
pip install awscurl
```

Then use it:
```bash
awscurl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"inputText": "Hello, how are you?"}' \
  https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke
```

---

## Method 4: Manual Curl with AWS Signature (Advanced)

AWS APIs require AWS Signature Version 4. Here's how to create a signed request manually:

### Step 1: Get AWS Credentials
```bash
aws configure list
```

### Step 2: Use the Python script to generate signed curl
```bash
python generate_signed_curl.py --input "Your message here"
```

The script will output a complete curl command with all necessary headers.

---

## Example: Complete Curl Command (Generated)

After running `generate_signed_curl.py`, you'll get something like:

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'Host: bedrock-agentcore.us-west-2.amazonaws.com' \
  -H 'X-Amz-Date: 20240101T120000Z' \
  -H 'Authorization: AWS4-HMAC-SHA256 Credential=...' \
  -d '{"inputText": "Hello, how are you?"}' \
  'https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke'
```

**Note:** The actual command will have real AWS credentials and timestamps.

---

## Request Format

### Standard Format
```json
{
  "inputText": "Your message here"
}
```

### With Session ID (for conversation context)
```json
{
  "inputText": "Your message here",
  "sessionId": "optional-session-id"
}
```

### Custom Format (matches your agent.py)
```json
{
  "prompt": "Your message here",
  "user": "user@example.com",
  "source": "email",
  "subject": "Optional subject"
}
```

---

## Testing

### Quick Test
```bash
# Using AWS CLI (easiest)
aws bedrock-agentcore invoke-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2 \
    --input '{"inputText": "Test message"}' \
    --output json | jq
```

### Using Generated Curl
```bash
# Generate and execute
python generate_signed_curl.py --input "Test message" --save test.sh
bash test.sh
```

---

## Troubleshooting

### "Access Denied" Error
- Check AWS credentials: `aws configure list`
- Verify IAM permissions for `bedrock-agentcore:InvokeAgent`
- Ensure you're using the correct region

### "Agent not found" Error
- Verify agent ID: `RitvikAgent-Nfl5014O49`
- Check region: `us-west-2`
- Ensure agent is deployed and active

### "Invalid Signature" Error
- Regenerate the curl command (signatures expire)
- Check system time is synchronized
- Verify AWS credentials are correct

---

## Security Notes

⚠️ **Important:**
- Signed curl commands contain AWS credentials in headers
- **Never commit these commands to version control**
- **Never share them publicly**
- Credentials expire, so regenerate as needed
- Use AWS CLI or the Python script for production use

---

## Alternative: Use AWS SDK Instead

For production applications, consider using AWS SDKs instead of curl:

**Python:**
```python
import boto3

client = boto3.client('bedrock-agentcore', region_name='us-west-2')
response = client.invoke_agent(
    agentId='RitvikAgent-Nfl5014O49',
    inputText='Hello'
)
```

**Node.js:**
```javascript
const { BedrockAgentCoreClient, InvokeAgentCommand } = require("@aws-sdk/client-bedrock-agentcore");

const client = new BedrockAgentCoreClient({ region: "us-west-2" });
const command = new InvokeAgentCommand({
  agentId: "RitvikAgent-Nfl5014O49",
  inputText: "Hello"
});

const response = await client.send(command);
```

