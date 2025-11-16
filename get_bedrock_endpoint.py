"""
Script to get Bedrock AgentCore endpoint information
"""
import boto3
import json
import sys
from pathlib import Path

def load_agent_config():
    """Load agent configuration from .bedrock_agentcore.yaml"""
    try:
        import yaml
        config_path = Path('.bedrock_agentcore.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
    except ImportError:
        print("Warning: PyYAML not installed. Install with: pip install pyyaml")
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
    return None

def get_agent_endpoint(agent_id=None, region=None):
    """
    Get the Bedrock AgentCore endpoint for an agent
    
    Args:
        agent_id: Agent ID (optional, will try to get from config)
        region: AWS region (optional, will try to get from config)
    
    Returns:
        dict with endpoint information
    """
    # Try to load from config
    config = load_agent_config()
    
    if not agent_id and config:
        # Get default agent name
        default_agent = config.get('default_agent', 'RitvikAgent')
        agent_config = config.get('agents', {}).get(default_agent, {})
        
        # Get agent ID from config
        bedrock_config = agent_config.get('bedrock_agentcore', {})
        agent_id = bedrock_config.get('agent_id') or bedrock_config.get('agent_arn', '').split('/')[-1]
        
        # Get region from config
        aws_config = agent_config.get('aws', {})
        region = region or aws_config.get('region', 'us-west-2')
    
    if not agent_id:
        print("Error: Agent ID not found. Please provide agent_id parameter or ensure .bedrock_agentcore.yaml exists.")
        return None
    
    if not region:
        region = 'us-west-2'
    
    # Construct endpoint URL
    endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com/agents/{agent_id}/invoke"
    
    # Try to get agent details from AWS
    try:
        client = boto3.client('bedrock-agentcore', region_name=region)
        response = client.get_agent(agentId=agent_id)
        agent_details = response.get('agent', {})
        
        return {
            'agent_id': agent_id,
            'agent_arn': agent_details.get('agentArn', ''),
            'agent_name': agent_details.get('agentName', ''),
            'region': region,
            'endpoint': endpoint,
            'status': agent_details.get('status', 'UNKNOWN'),
            'created_at': agent_details.get('createdAt', ''),
            'updated_at': agent_details.get('updatedAt', '')
        }
    except Exception as e:
        print(f"Warning: Could not fetch agent details from AWS: {e}")
        print("This might be due to:")
        print("  1. AWS credentials not configured")
        print("  2. Insufficient IAM permissions")
        print("  3. Agent not found")
        print(f"\nUsing constructed endpoint: {endpoint}")
        
        return {
            'agent_id': agent_id,
            'region': region,
            'endpoint': endpoint,
            'status': 'UNKNOWN (could not verify)'
        }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Get Bedrock AgentCore endpoint')
    parser.add_argument('--agent-id', help='Agent ID (optional, will use config if not provided)')
    parser.add_argument('--region', help='AWS region (optional, defaults to us-west-2)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    result = get_agent_endpoint(agent_id=args.agent_id, region=args.region)
    
    if not result:
        sys.exit(1)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 60)
        print("Bedrock AgentCore Endpoint Information")
        print("=" * 60)
        print(f"Agent ID:     {result.get('agent_id', 'N/A')}")
        if result.get('agent_name'):
            print(f"Agent Name:   {result.get('agent_name', 'N/A')}")
        if result.get('agent_arn'):
            print(f"Agent ARN:    {result.get('agent_arn', 'N/A')}")
        print(f"Region:       {result.get('region', 'N/A')}")
        print(f"Status:       {result.get('status', 'N/A')}")
        print(f"\nEndpoint URL:")
        print(f"  {result.get('endpoint', 'N/A')}")
        print("\n" + "=" * 60)
        print("\nExample usage:")
        print(f"\n  AWS CLI:")
        print(f"    aws bedrock-agentcore invoke-agent \\")
        print(f"      --agent-id {result.get('agent_id')} \\")
        print(f"      --region {result.get('region')} \\")
        print(f"      --input '{{\"prompt\": \"Hello\"}}'")
        print(f"\n  Python (boto3):")
        print(f"    import boto3")
        print(f"    client = boto3.client('bedrock-agentcore', region_name='{result.get('region')}')")
        print(f"    response = client.invoke_agent(")
        print(f"        agentId='{result.get('agent_id')}',")
        print(f"        inputText='Hello'")
        print(f"    )")
        print("=" * 60)

if __name__ == '__main__':
    main()

