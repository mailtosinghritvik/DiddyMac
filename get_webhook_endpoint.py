"""
Get your Bedrock AgentCore webhook endpoint
"""
import sys
from pathlib import Path

def get_endpoint():
    """Get the webhook endpoint URL"""
    # Load config
    try:
        import yaml
        config_path = Path('.bedrock_agentcore.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            default_agent = config.get('default_agent', 'RitvikAgent')
            agent_config = config.get('agents', {}).get(default_agent, {})
            bedrock_config = agent_config.get('bedrock_agentcore', {})
            aws_config = agent_config.get('aws', {})
            
            agent_id = bedrock_config.get('agent_id', 'RitvikAgent-Nfl5014O49')
            region = aws_config.get('region', 'us-west-2')
            
            endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com/agents/{agent_id}/invoke"
            
            return {
                'endpoint': endpoint,
                'agent_id': agent_id,
                'region': region
            }
    except ImportError:
        pass
    except Exception as e:
        print(f"Warning: Could not load config: {e}", file=sys.stderr)
    
    # Default values
    return {
        'endpoint': 'https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke',
        'agent_id': 'RitvikAgent-Nfl5014O49',
        'region': 'us-west-2'
    }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Get Bedrock AgentCore webhook endpoint')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()
    
    info = get_endpoint()
    
    if args.json:
        import json
        print(json.dumps(info, indent=2))
    else:
        print("=" * 70)
        print("Bedrock AgentCore Webhook Endpoint")
        print("=" * 70)
        print()
        print(f"Endpoint URL:")
        print(f"  {info['endpoint']}")
        print()
        print(f"Agent ID: {info['agent_id']}")
        print(f"Region:   {info['region']}")
        print()
        print("=" * 70)
        print()
        print("⚠️  IMPORTANT: This endpoint requires AWS Signature V4 authentication")
        print("   Most webhook services cannot use it directly.")
        print()
        print("Solutions:")
        print("  1. Use Make.com or n8n (support AWS auth)")
        print("  2. Deploy webhook_proxy.py as a proxy server")
        print("  3. Use AWS Lambda + API Gateway")
        print()
        print("See WEBHOOK_ENDPOINT_GUIDE.md for details")
        print("=" * 70)

if __name__ == '__main__':
    main()

