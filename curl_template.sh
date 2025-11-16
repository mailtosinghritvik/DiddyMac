#!/bin/bash
# Curl command template for Bedrock AgentCore
# NOTE: This is a template - you need to add AWS Signature headers
# Use get_curl_command.py to generate a properly signed version

# Correct endpoint (note: /invoke not /invocations)
ENDPOINT="https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke"

# Request body
BODY='{"inputText": "Hello, how are you?"}'

# Template format (this won't work without AWS signature headers)
curl --location --request POST "${ENDPOINT}" \
--header 'Content-Type: application/json' \
--header 'Host: bedrock-agentcore.us-west-2.amazonaws.com' \
--header 'X-Amz-Date: 20240101T120000Z' \
--header 'Authorization: AWS4-HMAC-SHA256 Credential=YOUR_ACCESS_KEY/20240101/us-west-2/bedrock-agentcore/aws4_request, SignedHeaders=content-type;host;x-amz-date, Signature=YOUR_SIGNATURE' \
--data "${BODY}"

# To get a properly signed version, run:
# python get_curl_command.py --input "Your message here"

