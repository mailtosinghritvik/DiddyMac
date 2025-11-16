# Bedrock Agent Lambda Function Guide

## New Lambda Function Created! ✅

A new, optimized Lambda function specifically for accessing your Bedrock AgentCore agent.

## Quick Deploy

### Windows:
```powershell
.\deploy_bedrock_lambda.ps1
```

### Linux/Mac:
```bash
chmod +x deploy_bedrock_lambda.sh
./deploy_bedrock_lambda.sh
```

## Function Details

**Function Name:** `bedrock-agent-lambda`  
**Handler:** `bedrock_agent_lambda.lambda_handler`  
**Runtime:** Python 3.11  
**Timeout:** 300 seconds  
**Memory:** 512 MB  

## Features

✅ **Optimized for Lambda** - Minimal dependencies, fast cold starts  
✅ **Multiple Event Sources** - API Gateway, Function URL, Direct invocation  
✅ **Flexible Input** - Accepts various input formats  
✅ **Error Handling** - Robust error responses  
✅ **CORS Enabled** - Works from browsers  
✅ **Singleton Client** - Reuses connection for performance  

## API Endpoints

After deployment, you'll get a Function URL:

```
https://xxxxxxxxxx.lambda-url.us-west-2.on.aws/
```

### Available Endpoints:

1. **Health Check**
   ```bash
   GET /health
   ```

2. **Status**
   ```bash
   GET /status
   ```

3. **Invoke Agent**
   ```bash
   POST /invoke
   Body: {"inputText": "Hello"}
   ```

4. **Webhook**
   ```bash
   POST /webhook
   Body: {"message": "Hello"}
   ```

## Usage Examples

### Using curl

```bash
# Health check
curl https://your-function-url.lambda-url.us-west-2.on.aws/health

# Invoke agent
curl -X POST https://your-function-url.lambda-url.us-west-2.on.aws/invoke \
  -H "Content-Type: application/json" \
  -d '{"inputText": "Hello, how are you?"}'

# With session
curl -X POST https://your-function-url.lambda-url.us-west-2.on.aws/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "inputText": "What is my name?",
    "sessionId": "your-session-id"
  }'
```

### Using Python

```python
import requests

url = "https://your-function-url.lambda-url.us-west-2.on.aws/invoke"

response = requests.post(
    url,
    json={"inputText": "Hello, how are you?"}
)

print(response.json())
```

### Using JavaScript

```javascript
fetch('https://your-function-url.lambda-url.us-west-2.on.aws/invoke', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    inputText: 'Hello, how are you?'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Direct Lambda Invocation

You can also invoke the Lambda directly (not via HTTP):

```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-west-2')

response = lambda_client.invoke(
    FunctionName='bedrock-agent-lambda',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'inputText': 'Hello, how are you?',
        'sessionId': 'optional-session-id'
    })
)

result = json.loads(response['Payload'].read())
print(result)
```

## Request Formats

### Standard Format
```json
{
  "inputText": "Your message here",
  "sessionId": "optional-session-id"
}
```

### Alternative Formats (also accepted)
```json
{
  "input": "Your message",
  "message": "Your message",
  "text": "Your message",
  "prompt": "Your message"
}
```

## Response Format

### Success Response
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "completion": "Agent's response...",
    "session_id": "session-id-if-provided",
    "payload": {...}
  }
}
```

### Error Response
```json
{
  "statusCode": 400,
  "body": {
    "success": false,
    "error": "Error message"
  }
}
```

## Environment Variables

The Lambda function uses these environment variables (set automatically):

- `AWS_REGION`: us-west-2
- `BEDROCK_AGENT_ID`: RitvikAgent-Nfl5014O49
- `AWS_ACCOUNT_ID`: 624571284647

You can override these in Lambda console if needed.

## Monitoring

### View Logs

```bash
aws logs tail /aws/lambda/bedrock-agent-lambda --follow --region us-west-2
```

### View Metrics

1. Go to AWS Console → Lambda → bedrock-agent-lambda
2. Click "Monitoring" tab
3. View invocations, errors, duration, etc.

## Update Function

```bash
# Update code
.\deploy_bedrock_lambda.ps1
```

Or manually:
```bash
zip -r bedrock_lambda_deployment.zip bedrock_agent_lambda.py utils/

aws lambda update-function-code \
    --function-name bedrock-agent-lambda \
    --zip-file fileb://bedrock_lambda_deployment.zip \
    --region us-west-2
```

## Cost

- **Free Tier**: 1M requests/month free
- **After Free Tier**: $0.20 per 1M requests
- **Compute**: $0.0000166667 per GB-second

Very cost-effective! 💰

## Troubleshooting

### Function Times Out

Increase timeout:
```bash
aws lambda update-function-configuration \
    --function-name bedrock-agent-lambda \
    --timeout 900 \
    --region us-west-2
```

### Out of Memory

Increase memory:
```bash
aws lambda update-function-configuration \
    --function-name bedrock-agent-lambda \
    --memory-size 1024 \
    --region us-west-2
```

### Permission Errors

Check IAM role has Bedrock permissions:
```bash
aws iam list-attached-role-policies \
    --role-name bedrock-agent-lambda-role
```

## Security

### Enable Authentication

Change Function URL auth type:
```bash
aws lambda update-function-url-config \
    --function-name bedrock-agent-lambda \
    --auth-type AWS_IAM \
    --region us-west-2
```

### Restrict CORS

Update CORS to specific origins:
```bash
aws lambda update-function-url-config \
    --function-name bedrock-agent-lambda \
    --cors '{"AllowOrigins": ["https://yourdomain.com"]}' \
    --region us-west-2
```

## Next Steps

1. ✅ Deploy: `.\deploy_bedrock_lambda.ps1`
2. ✅ Test: Use the Function URL
3. ✅ Integrate: Use in your applications/webhooks
4. ✅ Monitor: Check CloudWatch logs

Your Lambda function is ready to deploy! 🚀

