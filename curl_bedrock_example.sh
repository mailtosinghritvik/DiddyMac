#!/bin/bash
# Example curl commands for Bedrock AgentCore

# Configuration
AGENT_ID="RitvikAgent-Nfl5014O49"
REGION="us-west-2"
ENDPOINT="https://bedrock-agentcore.${REGION}.amazonaws.com/agents/${AGENT_ID}/invoke"

# Method 1: Using AWS CLI to sign the request (RECOMMENDED)
# This is the easiest way - AWS CLI handles the signing automatically
echo "Method 1: Using AWS CLI (Recommended)"
echo "======================================"
aws bedrock-agentcore invoke-agent \
    --agent-id ${AGENT_ID} \
    --region ${REGION} \
    --input '{"inputText": "Hello, how are you?"}' \
    --output json

echo ""
echo ""

# Method 2: Using AWS CLI to generate a presigned request
# This creates a curl command with all headers
echo "Method 2: Generate presigned curl command"
echo "=========================================="
# Note: Bedrock AgentCore doesn't support presigned URLs directly
# But we can use AWS CLI to show what the request looks like
echo "For Bedrock AgentCore, you need to sign requests with AWS Signature V4"
echo "Use the AWS CLI method above, or see Method 3 below"
echo ""

# Method 3: Manual curl with AWS Signature (requires awscurl or similar)
echo "Method 3: Using awscurl (if installed)"
echo "======================================"
echo "Install awscurl first: pip install awscurl"
echo ""
echo "Then use:"
echo "awscurl -X POST \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"inputText\": \"Hello, how are you?\"}' \\"
echo "  ${ENDPOINT}"
echo ""

# Method 4: Using Python to generate signed curl command
echo "Method 4: Python script to generate signed curl"
echo "================================================"
echo "See generate_signed_curl.py for a script that generates a signed curl command"
echo ""

