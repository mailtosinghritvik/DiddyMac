# Webhook Endpoint - Quick Start

## Your Webhook Endpoint

```
https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke
```

**Get it programmatically:**
```bash
python get_webhook_endpoint.py
```

---

## ⚠️ Important: AWS Authentication Required

This endpoint requires **AWS Signature V4 authentication**. Most webhook services (Zapier, etc.) cannot use it directly.

---

## Quick Solutions

### Option 1: Use Make.com or n8n (Easiest)

These services support AWS authentication natively:

**Make.com:**
1. Create HTTP Request module
2. URL: `https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke`
3. Authentication: AWS Signature V4
4. Region: `us-west-2`
5. Service: `bedrock-agentcore`

**n8n:**
1. Create HTTP Request node
2. Same configuration as above

### Option 2: Deploy Proxy Server (Recommended for Zapier)

Deploy `webhook_proxy.py` on Railway/Heroku:

```bash
# Deploy to Railway
railway init
railway up

# Or Heroku
heroku create your-webhook-proxy
git push heroku main
```

Then use the proxy URL as webhook (no AWS auth needed).

### Option 3: AWS Lambda Proxy

Deploy Lambda function with API Gateway - get a public webhook URL.

---

## Test Your Endpoint

```bash
# Get endpoint
python get_webhook_endpoint.py

# Test with Python
python -c "
from utils.bedrock_agentcore_client import invoke_bedrock_agent
result = invoke_bedrock_agent('Hello from webhook')
print(result)
"
```

---

## Request Format

```json
{
  "inputText": "Your message here",
  "sessionId": "optional-session-id"
}
```

---

## Full Documentation

See `WEBHOOK_ENDPOINT_GUIDE.md` for complete setup instructions.

