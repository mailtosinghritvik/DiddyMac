#!/bin/bash
# Deploy Bedrock AgentCore API to AWS Lambda

set -e

FUNCTION_NAME="bedrock-agentcore-api"
REGION="us-west-2"
RUNTIME="python3.11"
HANDLER="lambda_function.lambda_handler"
ROLE_NAME="bedrock-agentcore-lambda-role"

echo "=========================================="
echo "Deploying to AWS Lambda"
echo "=========================================="
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI not found. Install from https://aws.amazon.com/cli/"
    exit 1
fi

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &>/dev/null; then
    echo "Function exists, updating..."
    UPDATE_MODE=true
else
    echo "Function does not exist, creating..."
    UPDATE_MODE=false
fi

# Create deployment package
echo "Creating deployment package..."
zip -r deployment.zip . \
    -x "*.git*" \
    -x "*.pyc" \
    -x "__pycache__/*" \
    -x "*.md" \
    -x "*.sh" \
    -x "*.ps1" \
    -x "test_*" \
    -x "*.txt" \
    -x ".bedrock_agentcore/*" \
    -x "deployment.zip"

echo "Package created: deployment.zip"
echo ""

# Get or create IAM role
echo "Setting up IAM role..."
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ROLE_ARN" ]; then
    echo "Creating IAM role..."
    
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
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://trust-policy.json \
        --description "Role for Bedrock AgentCore Lambda function"
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Wait for role to be available
    echo "Waiting for role to be available..."
    sleep 5
    
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
    
    rm trust-policy.json
fi

echo "Using IAM role: $ROLE_ARN"
echo ""

# Deploy function
if [ "$UPDATE_MODE" = true ]; then
    echo "Updating Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://deployment.zip \
        --region $REGION
    
    echo "Waiting for update to complete..."
    aws lambda wait function-updated \
        --function-name $FUNCTION_NAME \
        --region $REGION
    
    echo "✓ Function updated!"
else
    echo "Creating Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://deployment.zip \
        --timeout 300 \
        --memory-size 512 \
        --region $REGION \
        --environment Variables="{AWS_REGION=$REGION}"
    
    echo "✓ Function created!"
fi

echo ""

# Get function URL or create API Gateway
echo "Setting up API endpoint..."

# Try to create function URL (simpler)
FUNCTION_URL=$(aws lambda get-function-url-config \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'FunctionUrl' \
    --output text 2>/dev/null || echo "")

if [ -z "$FUNCTION_URL" ]; then
    echo "Creating function URL..."
    aws lambda create-function-url-config \
        --function-name $FUNCTION_NAME \
        --auth-type NONE \
        --cors '{"AllowOrigins": ["*"], "AllowMethods": ["*"], "AllowHeaders": ["*"]}' \
        --region $REGION
    
    FUNCTION_URL=$(aws lambda get-function-url-config \
        --function-name $FUNCTION_NAME \
        --region $REGION \
        --query 'FunctionUrl' \
        --output text)
fi

echo ""
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo ""
echo "Function URL: $FUNCTION_URL"
echo ""
echo "Test endpoints:"
echo "  GET  $FUNCTION_URL/health"
echo "  GET  $FUNCTION_URL/status"
echo "  POST $FUNCTION_URL/invoke"
echo "  POST $FUNCTION_URL/webhook"
echo ""
echo "Example:"
echo "  curl -X POST $FUNCTION_URL/invoke \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"inputText\": \"Hello\"}'"
echo ""

# Cleanup
rm -f deployment.zip

