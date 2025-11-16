"""
Generate a signed curl command for Bedrock AgentCore
This script creates a curl command with AWS Signature Version 4 authentication
"""
import boto3
import json
import sys
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from datetime import datetime
import urllib.parse

def generate_signed_curl(agent_id, region, input_text, session_id=None):
    """
    Generate a curl command with AWS Signature V4 for Bedrock AgentCore
    
    Args:
        agent_id: Bedrock AgentCore agent ID
        region: AWS region
        input_text: Text to send to the agent
        session_id: Optional session ID for conversation context
    
    Returns:
        str: Complete curl command
    """
    # Get AWS credentials
    session = boto3.Session()
    credentials = session.get_credentials()
    
    if not credentials:
        print("Error: AWS credentials not found. Please configure AWS credentials.")
        print("Run: aws configure")
        sys.exit(1)
    
    # Construct endpoint
    endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com/agents/{agent_id}/invoke"
    
    # Prepare request body
    body = {
        "inputText": input_text
    }
    if session_id:
        body["sessionId"] = session_id
    
    body_json = json.dumps(body)
    
    # Create AWS request
    request = AWSRequest(
        method='POST',
        url=endpoint,
        data=body_json.encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Host': f'bedrock-agentcore.{region}.amazonaws.com'
        }
    )
    
    # Sign the request
    SigV4Auth(credentials, 'bedrock-agentcore', region).add_auth(request)
    
    # Extract headers
    headers = dict(request.headers)
    
    # Build curl command
    curl_headers = []
    for key, value in headers.items():
        curl_headers.append(f"  -H '{key}: {value}'")
    
    curl_command = f"""curl -X POST \\
  {chr(10).join(curl_headers)} \\
  -d '{body_json}' \\
  '{endpoint}'"""
    
    return curl_command

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate signed curl command for Bedrock AgentCore'
    )
    parser.add_argument(
        '--agent-id',
        default='RitvikAgent-Nfl5014O49',
        help='Agent ID (default: from config)'
    )
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input text to send to the agent'
    )
    parser.add_argument(
        '--session-id',
        help='Optional session ID for conversation context'
    )
    parser.add_argument(
        '--save',
        help='Save curl command to file'
    )
    
    args = parser.parse_args()
    
    try:
        curl_cmd = generate_signed_curl(
            agent_id=args.agent_id,
            region=args.region,
            input_text=args.input,
            session_id=args.session_id
        )
        
        print("=" * 70)
        print("Signed curl command for Bedrock AgentCore")
        print("=" * 70)
        print()
        print(curl_cmd)
        print()
        print("=" * 70)
        print("Note: This command includes AWS credentials in headers.")
        print("      Keep it secure and don't share it publicly.")
        print("=" * 70)
        
        if args.save:
            with open(args.save, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("# Auto-generated signed curl command\n")
                f.write("# Generated at: " + datetime.now().isoformat() + "\n")
                f.write("# WARNING: Contains AWS credentials - keep secure!\n\n")
                f.write(curl_cmd + "\n")
            print(f"\nCommand saved to: {args.save}")
            print("Make it executable: chmod +x " + args.save)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

