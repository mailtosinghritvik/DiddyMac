# Postman Setup Guide for Bedrock AgentCore

## Quick Setup

### Step 1: Import the Collection

1. Open Postman
2. Click **Import** button (top left)
3. Select the file: `Bedrock_AgentCore.postman_collection.json`
4. The collection will be imported with 3 example requests

### Step 2: Configure AWS Credentials

#### Option A: Using Collection Variables (Recommended)

1. Right-click on the collection: **Bedrock AgentCore - RitvikAgent**
2. Select **Edit**
3. Go to the **Variables** tab
4. Set the following variables:

```
AWS_ACCESS_KEY_ID = your-access-key-id
AWS_SECRET_ACCESS_KEY = your-secret-access-key
AWS_SESSION_TOKEN = (leave empty unless using temporary credentials)
```

5. Click **Save**

#### Option B: Using Environment Variables

1. Click **Environments** in the left sidebar
2. Click **+** to create a new environment
3. Name it: `AWS Bedrock`
4. Add these variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `AWS_ACCESS_KEY_ID` | your-access-key | your-access-key |
| `AWS_SECRET_ACCESS_KEY` | your-secret-key | your-secret-key |
| `AWS_SESSION_TOKEN` | (leave empty) | (leave empty) |

5. Select this environment from the dropdown (top right)

### Step 3: Verify Authentication

The collection is pre-configured with **AWS Signature Version 4** authentication:
- **Type**: AWS Signature
- **Service**: `bedrock-agentcore`
- **Region**: `us-west-2`
- **Access Key**: `{{AWS_ACCESS_KEY_ID}}`
- **Secret Key**: `{{AWS_SECRET_ACCESS_KEY}}`
- **Session Token**: `{{AWS_SESSION_TOKEN}}` (optional)

This is set at the collection level, so all requests will use it automatically.

---

## Available Requests

### 1. Invoke Agent - Simple
- **Method**: POST
- **URL**: `https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke`
- **Body**: Simple JSON with `inputText`

### 2. Invoke Agent - With Session
- Same as above but includes `sessionId` for conversation context

### 3. Invoke Agent - Custom Format
- Uses your custom format with `prompt`, `user`, `source`, `subject`

---

## Manual Setup (If Not Using Collection)

### Step 1: Create New Request

1. Click **New** → **HTTP Request**
2. Set method to **POST**
3. Enter URL:
```
https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke
```

### Step 2: Configure Authentication

1. Go to **Authorization** tab
2. Select **Type**: **AWS Signature**
3. Fill in:
   - **Access Key**: Your AWS Access Key ID
   - **Secret Key**: Your AWS Secret Access Key
   - **AWS Region**: `us-west-2`
   - **Service Name**: `bedrock-agentcore`
   - **Session Token**: (leave empty unless using temporary credentials)

### Step 3: Set Headers

1. Go to **Headers** tab
2. Add header:
   - **Key**: `Content-Type`
   - **Value**: `application/json`

### Step 4: Set Body

1. Go to **Body** tab
2. Select **raw**
3. Select **JSON** from dropdown
4. Enter request body:

```json
{
  "inputText": "Hello, how are you?"
}
```

Or with session:

```json
{
  "inputText": "Hello, how are you?",
  "sessionId": "your-session-id"
}
```

Or custom format:

```json
{
  "prompt": "Schedule a meeting tomorrow at 3pm",
  "user": "user@example.com",
  "source": "email",
  "subject": "Meeting Request"
}
```

### Step 5: Send Request

Click **Send** button

---

## Getting AWS Credentials

### Option 1: From AWS CLI (if configured)
```bash
aws configure list
```

### Option 2: From AWS Console
1. Go to AWS Console → IAM
2. Users → Your User → Security Credentials
3. Create Access Key

### Option 3: From Environment Variables
```bash
# Windows PowerShell
$env:AWS_ACCESS_KEY_ID
$env:AWS_SECRET_ACCESS_KEY

# Linux/Mac
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
```

---

## Example Request Bodies

### Simple Request
```json
{
  "inputText": "Hello, how are you?"
}
```

### With Session (for conversation context)
```json
{
  "inputText": "What did I ask you before?",
  "sessionId": "e89c4524-2e2b-4768-9a1c-4a3005528bb9"
}
```

### Custom Format (matches your agent.py)
```json
{
  "prompt": "Schedule a meeting with John tomorrow at 3pm",
  "user": "user@example.com",
  "source": "email",
  "subject": "Meeting Request",
  "phone_number": "+1234567890"
}
```

---

## Expected Response

A successful response will look like:

```json
{
  "completion": "...",
  "stopReason": "...",
  "trace": {...}
}
```

Or in your custom format:

```json
{
  "status": "success",
  "type": "...",
  "message": "...",
  "final_output": "..."
}
```

---

## Troubleshooting

### Error: "Access Denied"
- ✅ Check AWS credentials are correct
- ✅ Verify IAM permissions include `bedrock-agentcore:InvokeAgent`
- ✅ Ensure region is `us-west-2`

### Error: "Invalid Signature"
- ✅ Check system time is synchronized
- ✅ Verify service name is exactly `bedrock-agentcore`
- ✅ Ensure region is `us-west-2`

### Error: "Agent not found"
- ✅ Verify agent ID: `RitvikAgent-Nfl5014O49`
- ✅ Check agent is deployed and active
- ✅ Ensure correct region

### Error: "Connection refused" or timeout
- ✅ Check internet connectivity
- ✅ Verify endpoint URL is correct
- ✅ Check firewall settings

---

## Testing Tips

1. **Start with Simple Request**: Use the "Invoke Agent - Simple" request first
2. **Check Response**: Look at the response body and status code
3. **Use Session ID**: For multi-turn conversations, use the session ID from previous responses
4. **Save Examples**: Save successful requests as examples for reference
5. **Use Pre-request Scripts**: You can add scripts to generate session IDs automatically

---

## Pre-request Script Example (Optional)

To automatically generate a session ID, add this to **Pre-request Script** tab:

```javascript
// Generate a new session ID if not exists
if (!pm.collectionVariables.get("sessionId")) {
    const sessionId = pm.variables.replaceIn("{{$guid}}");
    pm.collectionVariables.set("sessionId", sessionId);
}

// Use the session ID in request body
const body = JSON.parse(pm.request.body.raw);
body.sessionId = pm.collectionVariables.get("sessionId");
pm.request.body.raw = JSON.stringify(body);
```

---

## Security Notes

⚠️ **Important:**
- Never commit Postman collections with real AWS credentials
- Use environment variables instead of hardcoding credentials
- Rotate credentials regularly
- Use IAM roles with least privilege principle
- Consider using temporary credentials for testing

---

## Quick Reference

**Endpoint:**
```
POST https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke
```

**Authentication:**
- Type: AWS Signature
- Service: `bedrock-agentcore`
- Region: `us-west-2`

**Headers:**
- `Content-Type: application/json`

**Agent Details:**
- Agent ID: `RitvikAgent-Nfl5014O49`
- Region: `us-west-2`
- Account: `624571284647`

