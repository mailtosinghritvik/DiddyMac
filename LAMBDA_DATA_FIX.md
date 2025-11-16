# Lambda Empty Data Fix

## Problem

When calling the agent from Lambda, rules were being created with **empty data** (NULL values for `user`, `source`, `input`, `subject` in the database).

This happened because:
1. Lambda was only sending `inputText` to Bedrock AgentCore
2. The agent expects `user`, `source`, `input` (or `prompt`), and `subject` fields
3. When these fields were missing, the database got NULL values

## Solution

Updated the Lambda function to:
1. ✅ Accept `user`, `source`, and `subject` fields in requests
2. ✅ Provide default values if not provided
3. ✅ Format the payload correctly with all required fields
4. ✅ Send `prompt` instead of `inputText` so agent.py Format 2 handles it

## Changes Made

### 1. Updated `invoke()` method
- Now accepts `user`, `source`, `subject` parameters
- Formats payload with `prompt`, `user`, `source`, `subject` fields
- Uses defaults: `lambda@example.com` for user, `lambda` for source

### 2. Updated `handle_invoke_request()`
- Extracts `user`, `source`, `subject` from request body
- Provides defaults if not present
- Passes all fields to `invoke()` method

### 3. Updated `handle_webhook_request()`
- Extracts and passes user, source, subject fields
- Uses `webhook@example.com` as default user

### 4. Updated `handle_direct_invocation()`
- Extracts user, source, subject from event
- Passes all fields to handler

## Request Format

### Standard Request (with all fields)
```json
{
  "inputText": "Create a rule to always send meeting summaries",
  "user": "user@example.com",
  "source": "lambda",
  "subject": "Rule Creation Request"
}
```

### Minimal Request (uses defaults)
```json
{
  "inputText": "Create a rule to always send meeting summaries"
}
```

Will automatically use:
- `user`: `lambda@example.com`
- `source`: `lambda`
- `subject`: `null`

## Testing

After redeploying the Lambda function:

```bash
# Test with all fields
curl -X POST https://your-function-url.lambda-url.us-west-2.on.aws/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "inputText": "Create a rule to always send meeting summaries",
    "user": "test@example.com",
    "source": "lambda",
    "subject": "Test Rule"
  }'

# Test with minimal fields (uses defaults)
curl -X POST https://your-function-url.lambda-url.us-west-2.on.aws/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "inputText": "Create a rule to always send meeting summaries"
  }'
```

## Expected Result

After the fix, database records should have:
- ✅ `user`: `lambda@example.com` (or provided value)
- ✅ `source`: `lambda` (or provided value)
- ✅ `input`: The input text
- ✅ `subject`: Provided value or NULL

No more empty data! 🎉

## Redeploy

After making these changes, redeploy the Lambda function:

```powershell
.\deploy_bedrock_lambda.ps1
```

Or manually update:
```bash
zip bedrock_lambda_deployment.zip bedrock_agent_lambda.py
aws lambda update-function-code \
    --function-name bedrock-agent-lambda \
    --zip-file fileb://bedrock_lambda_deployment.zip \
    --region us-west-2
```


