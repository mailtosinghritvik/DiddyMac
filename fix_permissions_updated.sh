#!/bin/bash
# Fix Lambda IAM Permissions for Bedrock AgentCore (Updated with wildcard)
# This script adds the necessary permissions including runtime-endpoint access

set -e

ROLE_NAME="TestlambdaforAgent-role-xmq700mb"
REGION="us-west-2"
ACCOUNT_ID="624571284647"
AGENT_ID="RitvikAgent-Nfl5014O49"

echo "=========================================="
echo "Fixing Lambda IAM Permissions (Updated)"
echo "=========================================="
echo ""

# Check if role exists
echo "Checking IAM role..."
if ! aws iam get-role --role-name $ROLE_NAME &>/dev/null; then
    echo "ERROR: Role '$ROLE_NAME' not found"
    exit 1
fi
echo "✓ Role found: $ROLE_NAME"
echo ""

# Create/Update Bedrock AgentCore policy with wildcard for runtime-endpoint
POLICY_NAME="BedrockAgentCoreInvokePolicy"
echo "Creating/updating Bedrock policy with wildcard support..."

cat > /tmp/bedrock-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:us-west-2:${ACCOUNT_ID}:runtime/${AGENT_ID}",
        "arn:aws:bedrock-agentcore:us-west-2:${ACCOUNT_ID}:runtime/${AGENT_ID}/*"
      ]
    }
  ]
}
EOF

# Check if policy exists
POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text 2>/dev/null || echo "")

if [ -n "$POLICY_ARN" ]; then
    echo "Policy exists, creating new version..."
    
    # Create new policy version
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document file:///tmp/bedrock-policy.json \
        --set-as-default > /dev/null
    
    echo "✓ Policy updated: $POLICY_ARN"
else
    # Create new policy
    echo "Creating new policy..."
    POLICY_ARN=$(aws iam create-policy \
        --policy-name $POLICY_NAME \
        --policy-document file:///tmp/bedrock-policy.json \
        --query 'Policy.Arn' \
        --output text)
    
    echo "✓ Policy created: $POLICY_ARN"
fi

echo ""

# Detach old policy if attached, then attach new one
echo "Updating role permissions..."

# Check if policy is attached
ATTACHED=$(aws iam list-attached-role-policies --role-name $ROLE_NAME --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" --output text)

if [ -n "$ATTACHED" ]; then
    echo "Policy already attached, detaching and reattaching..."
    aws iam detach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn "$POLICY_ARN" 2>/dev/null || true
    sleep 2
fi

# Attach policy to role
echo "Attaching policy to role..."
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn "$POLICY_ARN"

echo "✓ Policy attached to role!"
echo ""

# Also ensure basic Lambda execution role is attached
echo "Checking Lambda execution permissions..."
BASIC_EXECUTION_POLICY="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn $BASIC_EXECUTION_POLICY 2>/dev/null || echo "Basic execution policy already attached"

echo "✓ Lambda execution permissions OK"
echo ""

# Cleanup
rm -f /tmp/bedrock-policy.json

echo "=========================================="
echo "✓ Permissions Fixed!"
echo "=========================================="
echo ""
echo "Policy now includes:"
echo "  - arn:aws:bedrock-agentcore:us-west-2:${ACCOUNT_ID}:runtime/${AGENT_ID}"
echo "  - arn:aws:bedrock-agentcore:us-west-2:${ACCOUNT_ID}:runtime/${AGENT_ID}/*"
echo ""
echo "This covers both runtime and runtime-endpoint resources."
echo ""
echo "IMPORTANT: Wait 30-60 seconds for IAM permissions to fully propagate."
echo "Then test your Lambda function again."
echo ""

