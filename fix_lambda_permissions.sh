#!/bin/bash
# Fix Lambda IAM Permissions for Bedrock AgentCore

set -e

ROLE_NAME="TestlambdaforAgent-role-xmq700mb"  # Your existing role name
REGION="us-west-2"
ACCOUNT_ID="624571284647"
AGENT_ID="RitvikAgent-Nfl5014O49"

echo "=========================================="
echo "Fixing Lambda IAM Permissions"
echo "=========================================="
echo ""

# Check if role exists
echo "Checking IAM role..."
if ! aws iam get-role --role-name $ROLE_NAME &>/dev/null; then
    echo "ERROR: Role '$ROLE_NAME' not found"
    echo "Please check the role name in your Lambda function configuration"
    exit 1
fi
echo "✓ Role found: $ROLE_NAME"
echo ""

# Create Bedrock AgentCore policy
POLICY_NAME="BedrockAgentCoreInvokePolicy"
echo "Creating/updating Bedrock policy..."

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

if [ -z "$POLICY_ARN" ]; then
    # Create new policy
    POLICY_ARN=$(aws iam create-policy \
        --policy-name $POLICY_NAME \
        --policy-document file:///tmp/bedrock-policy.json \
        --query 'Policy.Arn' \
        --output text)
    echo "✓ Policy created: $POLICY_ARN"
else
    echo "✓ Policy exists: $POLICY_ARN"
fi

echo ""

# Attach policy to role
echo "Attaching policy to role..."
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn $POLICY_ARN

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
echo "The Lambda role now has permission to invoke Bedrock AgentCore."
echo ""
echo "Note: It may take a few seconds for permissions to propagate."
echo "If you still get errors, wait 10-30 seconds and try again."
echo ""

