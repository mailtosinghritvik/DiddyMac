#!/bin/bash
# Deploy Bedrock AgentCore Lambda Function
# Simple deployment script for the new Lambda function

set -e

FUNCTION_NAME="bedrock-agent-lambda"
REGION="us-west-2"
RUNTIME="python3.11"
HANDLER="bedrock_agent_lambda.lambda_handler"
ROLE_NAME="bedrock-agent-lambda-role"
ZIP_FILE="bedrock_lambda_deployment.zip"

echo "=========================================="
echo "Deploying Bedrock Agent Lambda Function"
echo "=========================================="
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI not found"
    exit 1
fi

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &>/dev/null 2>&1; then
    echo "✓ Function exists, will update..."
    UPDATE_MODE=true
else
    echo "✓ Function does not exist, will create..."
    UPDATE_MODE=false
fi

# Create deployment package
echo ""
echo "Creating deployment package..."
rm -f $ZIP_FILE

# Include just the Lambda function (self-contained, no utils dependency)
zip $ZIP_FILE bedrock_agent_lambda.py

echo "✓ Package created: $ZIP_FILE"
echo ""

# Get or create IAM role
echo "Setting up IAM role..."
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ROLE_ARN" ]; then
    echo "Creating IAM role..."
    
    # Trust policy
    cat > /tmp/trust-policy.json <<EOF
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

    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --description "Role for Bedrock Agent Lambda function"
    
    # Attach basic execution policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    sleep 5
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
    
    rm /tmp/trust-policy.json
    echo "✓ Role created: $ROLE_ARN"
else
    echo "✓ Using existing role: $ROLE_ARN"
fi

# Add Bedrock permissions to role
echo ""
echo "Configuring Bedrock permissions..."

ACCOUNT_ID="624571284647"
AGENT_ID="RitvikAgent-Nfl5014O49"
POLICY_NAME="BedrockAgentCoreInvokePolicy"

# Check if policy exists
POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text 2>/dev/null || echo "")

if [ -z "$POLICY_ARN" ]; then
    echo "Creating Bedrock policy..."
    cat > /tmp/bedrock-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": "arn:aws:bedrock-agentcore:us-west-2:${ACCOUNT_ID}:runtime/${AGENT_ID}"
    }
  ]
}
EOF

    POLICY_ARN=$(aws iam create-policy \
        --policy-name $POLICY_NAME \
        --policy-document file:///tmp/bedrock-policy.json \
        --query 'Policy.Arn' \
        --output text)
    
    rm /tmp/bedrock-policy.json
    echo "✓ Policy created: $POLICY_ARN"
else
    echo "✓ Policy exists: $POLICY_ARN"
fi

# Attach policy to role
echo "Attaching policy to role..."
if aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn $POLICY_ARN 2>/dev/null; then
    echo "✓ Policy attached to role"
else
    # Check if already attached
    ATTACHED=$(aws iam list-attached-role-policies --role-name $ROLE_NAME --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" --output text)
    if [ -n "$ATTACHED" ]; then
        echo "✓ Policy already attached"
    else
        echo "⚠ Warning: Could not attach policy (may need manual attachment)"
    fi
fi

echo "✓ Permissions configured"
echo ""

# Deploy function
if [ "$UPDATE_MODE" = true ]; then
    echo "Updating Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://$ZIP_FILE \
        --region $REGION > /dev/null
    
    echo "Waiting for update..."
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
        --zip-file fileb://$ZIP_FILE \
        --timeout 300 \
        --memory-size 512 \
        --region $REGION \
        --environment "Variables={AWS_REGION=$REGION,BEDROCK_AGENT_ID=RitvikAgent-Nfl5014O49,AWS_ACCOUNT_ID=624571284647}" > /dev/null
    
    echo "✓ Function created!"
fi

echo ""

# Create or get Function URL
echo "Setting up Function URL..."
FUNCTION_URL=$(aws lambda get-function-url-config \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'FunctionUrl' \
    --output text 2>/dev/null || echo "")

if [ -z "$FUNCTION_URL" ]; then
    echo "Creating Function URL..."
    aws lambda create-function-url-config \
        --function-name $FUNCTION_NAME \
        --auth-type NONE \
        --cors '{"AllowOrigins": ["*"], "AllowMethods": ["*"], "AllowHeaders": ["*"]}' \
        --region $REGION > /dev/null
    
    FUNCTION_URL=$(aws lambda get-function-url-config \
        --function-name $FUNCTION_NAME \
        --region $REGION \
        --query 'FunctionUrl' \
        --output text)
    
    echo "✓ Function URL created!"
else
    echo "✓ Function URL exists"
fi

echo ""
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo ""
echo "Function Name: $FUNCTION_NAME"
echo "Function URL:  $FUNCTION_URL"
echo ""
echo "Test endpoints:"
echo "  GET  $FUNCTION_URL/health"
echo "  GET  $FUNCTION_URL/status"
echo "  POST $FUNCTION_URL/invoke"
echo "  POST $FUNCTION_URL/webhook"
echo ""
echo "Example test:"
echo "  curl -X POST $FUNCTION_URL/invoke \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"inputText\": \"Hello\"}'"
echo ""

# Cleanup
rm -f $ZIP_FILE

