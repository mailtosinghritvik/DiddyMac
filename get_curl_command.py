"""
Generate curl command in the requested format for Bedrock AgentCore
"""
import boto3
import json
import sys
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

def generate_curl_command(agent_id, region, input_text, session_id=None):
    """
    Generate curl command with AWS Signature V4 in the requested format
    """
    # Get AWS credentials
    session = boto3.Session()
    credentials = session.get_credentials()
    
    if not credentials:
        print("Error: AWS credentials not found. Please configure AWS credentials.")
        print("Run: aws configure")
        sys.exit(1)
    
    # Construct endpoint - Note: correct path is /invoke (not /invocations)
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
    
    # Build curl command in the requested format
    curl_headers = []
    for key, value in headers.items():
        # Escape single quotes in header values for shell
        escaped_value = value.replace("'", "'\\''")
        curl_headers.append(f"--header '{key}: {escaped_value}'")
    
    # Format in the requested style (using --location --request POST)
    curl_command = f"""curl --location --request POST '{endpoint}' \\
{chr(10).join(curl_headers)} \\
--data '{body_json}'"""
    
    return curl_command

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate curl command for Bedrock AgentCore'
    )
    parser.add_argument(
        '--agent-id',
        default='RitvikAgent-Nfl5014O49',
        help='Agent ID (default: RitvikAgent-Nfl5014O49)'
    )
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    parser.add_argument(
        '--input',
        default='Hello, how are you?',
        help='Input text to send to the agent'
    )
    parser.add_argument(
        '--session-id',
        help='Optional session ID for conversation context'
    )
    
    args = parser.parse_args()
    
    try:
        curl_cmd = generate_curl_command(
            agent_id=args.agent_id,
            region=args.region,
            input_text=args.input,
            session_id=args.session_id
        )
        
        print(curl_cmd)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

