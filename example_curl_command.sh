#!/bin/bash
# Example curl command in your requested format
# NOTE: This needs AWS Signature headers to work
# Run: python get_curl_command.py --input "Your message" to get a signed version

# Your requested format (template - needs AWS signature headers):
curl --location --request POST 'https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke' \
--header 'Content-Type: application/json' \
--data '{"inputText": "Hello, how are you?"}'

# To get a working version with AWS signature, run:
# python get_curl_command.py --input "Hello, how are you?"

