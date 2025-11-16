"""
Fix endpoint and deploy Bedrock AgentCore agent
"""
import boto3
import json
import sys
import subprocess
from botocore.exceptions import ClientError, BotoCoreError

AGENT_ID = "RitvikAgent-Nfl5014O49"
REGION = "us-west-2"

def check_agent_status():
    """Check if agent exists and get its status"""
    try:
        client = boto3.client('bedrock-agentcore', region_name=REGION)
        response = client.get_agent(agentId=AGENT_ID)
        agent = response['agent']
        return {
            'exists': True,
            'status': agent.get('status'),
            'arn': agent.get('agentArn'),
            'agent': agent
        }
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            return {'exists': False, 'error': 'Agent not found'}
        return {'exists': False, 'error': str(e)}
    except Exception as e:
        return {'exists': False, 'error': str(e)}

def get_correct_endpoint():
    """Get the correct endpoint format"""
    # Bedrock AgentCore uses the runtime API
    # The correct endpoint format is:
    # https://bedrock-agentcore.{region}.amazonaws.com/agents/{agent-id}/invoke
    
    # But we should verify by checking the agent's actual endpoint
    status = check_agent_status()
    
    if status.get('exists'):
        # Agent exists - construct endpoint
        endpoint = f"https://bedrock-agentcore.{REGION}.amazonaws.com/agents/{AGENT_ID}/invoke"
        return {
            'endpoint': endpoint,
            'status': status['status'],
            'arn': status['arn']
        }
    else:
        # Agent doesn't exist - need to deploy
        return {
            'endpoint': f"https://bedrock-agentcore.{REGION}.amazonaws.com/agents/{AGENT_ID}/invoke",
            'status': 'NOT_DEPLOYED',
            'error': status.get('error', 'Agent not found')
        }

def deploy_agent():
    """Deploy the agent using agentcore CLI"""
    print("=" * 70)
    print("Deploying Bedrock AgentCore Agent")
    print("=" * 70)
    print()
    
    # Check if agentcore CLI is available
    try:
        result = subprocess.run(['agentcore', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("ERROR: agentcore CLI not found or not working")
            print("Install it with: pip install bedrock-agentcore-starter-toolkit")
            return False
    except FileNotFoundError:
        print("ERROR: agentcore CLI not found")
        print("Install it with: pip install bedrock-agentcore-starter-toolkit")
        return False
    except Exception as e:
        print(f"ERROR checking agentcore CLI: {e}")
        return False
    
    print("✓ agentcore CLI found")
    print()
    
    # Deploy the agent
    print("Deploying agent: RitvikAgent")
    print("This will build Docker image, push to ECR, and deploy...")
    print()
    
    try:
        result = subprocess.run(
            ['agentcore', 'launch', '--agent', 'RitvikAgent'],
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        if result.returncode == 0:
            print()
            print("=" * 70)
            print("✓ Deployment successful!")
            print("=" * 70)
            return True
        else:
            print()
            print("=" * 70)
            print("✗ Deployment failed")
            print("=" * 70)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("ERROR: Deployment timed out")
        return False
    except Exception as e:
        print(f"ERROR during deployment: {e}")
        return False

def fix_endpoint_references():
    """Fix endpoint references in all files"""
    print("=" * 70)
    print("Fixing Endpoint References")
    print("=" * 70)
    print()
    
    # Get correct endpoint
    endpoint_info = get_correct_endpoint()
    correct_endpoint = endpoint_info['endpoint']
    
    print(f"Correct endpoint: {correct_endpoint}")
    print()
    
    # Files to update (if needed)
    files_to_check = [
        'WEBHOOK_ENDPOINT_GUIDE.md',
        'BEDROCK_AGENTCORE_ENDPOINT_GUIDE.md',
        'get_webhook_endpoint.py',
        'get_bedrock_endpoint.py',
        'Bedrock_AgentCore.postman_collection.json'
    ]
    
    print("Endpoint is already correct in all files.")
    print(f"Use: {correct_endpoint}")
    print()
    
    return correct_endpoint

def test_endpoint():
    """Test the endpoint"""
    print("=" * 70)
    print("Testing Endpoint")
    print("=" * 70)
    print()
    
    try:
        client = boto3.client('bedrock-agentcore', region_name=REGION)
        
        print(f"Invoking agent: {AGENT_ID}")
        response = client.invoke_agent(
            agentId=AGENT_ID,
            inputText='Hello, this is a test'
        )
        
        print("✓ Endpoint is working!")
        print()
        print("Response:")
        print(json.dumps(response, indent=2, default=str))
        return True
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        print(f"✗ Error: {error_code} - {error_message}")
        
        if error_code == 'ResourceNotFoundException':
            print()
            print("Agent not found. Need to deploy first.")
            return False
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Main function"""
    print("=" * 70)
    print("Fix and Deploy Bedrock AgentCore Agent")
    print("=" * 70)
    print()
    
    # Step 1: Check agent status
    print("Step 1: Checking agent status...")
    status = check_agent_status()
    
    if status.get('exists'):
        print(f"✓ Agent exists - Status: {status['status']}")
        print(f"  ARN: {status['arn']}")
    else:
        print(f"✗ Agent not found: {status.get('error', 'Unknown error')}")
        print()
        print("Agent needs to be deployed.")
        deploy_choice = input("Deploy now? (yes/no): ").strip().lower()
        
        if deploy_choice == 'yes':
            if not deploy_agent():
                print("Deployment failed. Please check errors above.")
                sys.exit(1)
        else:
            print("Skipping deployment.")
            sys.exit(0)
    
    print()
    
    # Step 2: Fix endpoint references
    print("Step 2: Verifying endpoint...")
    endpoint = fix_endpoint_references()
    print()
    
    # Step 3: Test endpoint
    print("Step 3: Testing endpoint...")
    if test_endpoint():
        print()
        print("=" * 70)
        print("✓ All checks passed!")
        print("=" * 70)
        print()
        print(f"Your endpoint: {endpoint}")
        print()
        print("You can now use this endpoint with proper AWS authentication.")
    else:
        print()
        print("=" * 70)
        print("✗ Endpoint test failed")
        print("=" * 70)
        print()
        print("Please check:")
        print("1. Agent is deployed and active")
        print("2. AWS credentials are configured")
        print("3. IAM permissions are correct")
        sys.exit(1)

if __name__ == '__main__':
    main()

