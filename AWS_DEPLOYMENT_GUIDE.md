# AWS Deployment Guide for Bedrock AgentCore API

## Deployment Options

### Option 1: AWS Lambda + Function URL (Recommended - Easiest)

**Pros:**
- ✅ Serverless (no servers to manage)
- ✅ Pay per request (cost-effective)
- ✅ Auto-scaling
- ✅ Easy deployment

**Deploy:**
```bash
# Windows
.\deploy_lambda.ps1

# Linux/Mac
./deploy_lambda.sh
```

### Option 2: AWS Lambda + API Gateway

More control over API Gateway features (custom domains, rate limiting, etc.)

### Option 3: AWS App Runner

Container-based deployment (if you prefer containers)

### Option 4: AWS ECS/Fargate

For more control and container orchestration

---

## Quick Deploy: Lambda + Function URL

### Prerequisites

1. **AWS CLI configured:**
   ```bash
   aws configure
   ```

2. **IAM Permissions:**
   - `lambda:*`
   - `iam:CreateRole`, `iam:AttachRolePolicy`
   - `bedrock-agentcore:InvokeAgentRuntime`

### Deploy

```bash
# Windows PowerShell
.\deploy_lambda.ps1

# Linux/Mac
chmod +x deploy_lambda.sh
./deploy_lambda.sh
```

### What Gets Created

1. **Lambda Function**: `bedrock-agentcore-api`
2. **IAM Role**: `bedrock-agentcore-lambda-role`
3. **Function URL**: Public HTTPS endpoint

### After Deployment

You'll get a Function URL like:
```
https://xxxxxxxxxx.lambda-url.us-west-2.on.aws/
```

**Test it:**
```bash
curl https://xxxxxxxxxx.lambda-url.us-west-2.on.aws/health
```

---

## Manual Lambda Deployment

### Step 1: Create Deployment Package

```bash
# Create zip file
zip -r deployment.zip . \
    -x "*.git*" \
    -x "*.pyc" \
    -x "__pycache__/*" \
    -x "*.md" \
    -x "test_*" \
    -x "deployment.zip"
```

### Step 2: Create IAM Role

```bash
# Create trust policy
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
    --role-name bedrock-agentcore-lambda-role \
    --assume-role-policy-document file://trust-policy.json

# Attach execution policy
aws iam attach-role-policy \
    --role-name bedrock-agentcore-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name bedrock-agentcore-lambda-role --query 'Role.Arn' --output text)
```

### Step 3: Create Lambda Function

```bash
aws lambda create-function \
    --function-name bedrock-agentcore-api \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://deployment.zip \
    --timeout 300 \
    --memory-size 512 \
    --region us-west-2
```

### Step 4: Create Function URL

```bash
aws lambda create-function-url-config \
    --function-name bedrock-agentcore-api \
    --auth-type NONE \
    --cors '{"AllowOrigins": ["*"], "AllowMethods": ["*"], "AllowHeaders": ["*"]}' \
    --region us-west-2

# Get URL
aws lambda get-function-url-config \
    --function-name bedrock-agentcore-api \
    --region us-west-2 \
    --query 'FunctionUrl' \
    --output text
```

### Step 5: Add Bedrock Permissions

```bash
# Create policy for Bedrock AgentCore
cat > bedrock-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": "arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49"
    }
  ]
}
EOF

# Create policy
aws iam create-policy \
    --policy-name BedrockAgentCoreInvokePolicy \
    --policy-document file://bedrock-policy.json

# Attach to role
POLICY_ARN=$(aws iam list-policies --query 'Policies[?PolicyName==`BedrockAgentCoreInvokePolicy`].Arn' --output text)
aws iam attach-role-policy \
    --role-name bedrock-agentcore-lambda-role \
    --policy-arn $POLICY_ARN
```

---

## Update Lambda Function

```bash
# Update code
zip -r deployment.zip . -x "*.git*" -x "*.pyc" -x "__pycache__/*"
aws lambda update-function-code \
    --function-name bedrock-agentcore-api \
    --zip-file fileb://deployment.zip \
    --region us-west-2
```

---

## Testing Deployed API

### Health Check

```bash
curl https://your-function-url.lambda-url.us-west-2.on.aws/health
```

### Invoke Agent

```bash
curl -X POST https://your-function-url.lambda-url.us-west-2.on.aws/invoke \
  -H "Content-Type: application/json" \
  -d '{"inputText": "Hello, how are you?"}'
```

### Webhook

```bash
curl -X POST https://your-function-url.lambda-url.us-west-2.on.aws/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from webhook"}'
```

---

## Monitoring

### View Logs

```bash
# CloudWatch Logs
aws logs tail /aws/lambda/bedrock-agentcore-api --follow --region us-west-2
```

### View Metrics

1. Go to AWS Console → Lambda → bedrock-agentcore-api
2. Click "Monitoring" tab
3. View invocations, errors, duration, etc.

---

## Cost Estimation

**Lambda Pricing (us-west-2):**
- First 1M requests/month: Free
- $0.20 per 1M requests after
- $0.0000166667 per GB-second

**Example:**
- 100K requests/month: **Free**
- 1M requests/month: **Free**
- 10M requests/month: ~$1.80 + compute time

Very cost-effective for most use cases!

---

## Troubleshooting

### Function Times Out

Increase timeout:
```bash
aws lambda update-function-configuration \
    --function-name bedrock-agentcore-api \
    --timeout 900 \
    --region us-west-2
```

### Out of Memory

Increase memory:
```bash
aws lambda update-function-configuration \
    --function-name bedrock-agentcore-api \
    --memory-size 1024 \
    --region us-west-2
```

### Permission Errors

Check IAM role has Bedrock permissions:
```bash
aws iam list-attached-role-policies \
    --role-name bedrock-agentcore-lambda-role
```

### Function URL Not Working

Check CORS configuration:
```bash
aws lambda get-function-url-config \
    --function-name bedrock-agentcore-api \
    --region us-west-2
```

---

## Alternative: API Gateway

For more advanced features (custom domains, API keys, rate limiting):

1. Create API Gateway REST API
2. Create Lambda integration
3. Deploy to stage
4. Get API endpoint

See AWS documentation for API Gateway setup.

---

## Security Best Practices

1. **Enable Auth**: Change `auth-type` from `NONE` to `AWS_IAM`
2. **CORS**: Configure specific origins instead of `*`
3. **API Keys**: Use API Gateway with API keys
4. **VPC**: Deploy Lambda in VPC if needed
5. **Secrets**: Use AWS Secrets Manager for sensitive data

---

## Next Steps

1. ✅ Deploy: `.\deploy_lambda.ps1`
2. ✅ Test: Use the Function URL
3. ✅ Monitor: Check CloudWatch logs
4. ✅ Integrate: Use URL in webhooks/apps

Your API is now live on AWS! 🚀

