# Curl Command Format Examples

## Your Requested Format

Based on your example, here's the curl command in that format:

### ⚠️ Important Notes:
1. **Endpoint Path**: The correct path is `/invoke` (singular), not `/invocations` (plural)
2. **Agent ID**: The full agent ID is `RitvikAgent-Nfl5014O49`, not just `RitvikAgent`
3. **AWS Signature**: AWS requires Signature V4 authentication headers

---

## Template (Without AWS Signature - Won't Work)

```bash
curl --location --request POST 'https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke' \
--header 'Content-Type: application/json' \
--data '{"inputText": "Hello, how are you?"}'
```

**This won't work** because AWS requires authentication headers.

---

## Generate Properly Signed Curl Command

Use the Python script to generate a curl command with all AWS Signature headers:

```bash
# Basic usage
python get_curl_command.py --input "Hello, how are you?"

# With custom message
python get_curl_command.py --input "Schedule a meeting tomorrow at 3pm"

# With session ID
python get_curl_command.py --input "What did I ask before?" --session-id "your-session-id"
```

This will output a complete curl command in your requested format with all necessary AWS authentication headers.

---

## Example Output (Generated)

After running the script, you'll get something like:

```bash
curl --location --request POST 'https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke' \
--header 'Content-Type: application/json' \
--header 'Host: bedrock-agentcore.us-west-2.amazonaws.com' \
--header 'X-Amz-Date: 20240101T120000Z' \
--header 'Authorization: AWS4-HMAC-SHA256 Credential=AKIAIOSFODNN7EXAMPLE/20240101/us-west-2/bedrock-agentcore/aws4_request, SignedHeaders=content-type;host;x-amz-date, Signature=abc123...' \
--data '{"inputText": "Hello, how are you?"}'
```

---

## Alternative: Using Your Format with Different Endpoints

If you want to use `/invocations` (plural) as in your example, here's the format:

```bash
# Note: This endpoint path may not work - verify with AWS documentation
curl --location --request POST 'https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invocations' \
--header 'Content-Type: application/json' \
--data '{"inputText": "Hello, how are you?"}'
```

**However**, based on AWS Bedrock AgentCore documentation, the standard endpoint is `/invoke` (singular).

---

## Quick Reference

**Correct Endpoint:**
```
https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke
```

**Agent ID:** `RitvikAgent-Nfl5014O49`  
**Region:** `us-west-2`

**Request Body Examples:**

Simple:
```json
{"inputText": "Hello, how are you?"}
```

With Session:
```json
{"inputText": "Hello", "sessionId": "your-session-id"}
```

Custom Format:
```json
{"prompt": "Schedule a meeting", "user": "user@example.com", "source": "email"}
```

---

## Generate Now

Run this command to get a ready-to-use curl command:

```bash
python get_curl_command.py --input "Your message here"
```

Copy and paste the output directly into your terminal!

