"""
AWS Lambda function for Bedrock AgentCore API
Deploy this to Lambda with API Gateway
"""
import json
import logging
from typing import Dict, Any

# Lambda handler expects specific imports
try:
    from utils.bedrock_agentcore_client import BedrockAgentCoreClient
except ImportError:
    # For Lambda, we need to ensure the path is correct
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from utils.bedrock_agentcore_client import BedrockAgentCoreClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize client (reused across invocations)
bedrock_client = None

def get_client():
    """Get or create Bedrock client (reused for performance)"""
    global bedrock_client
    if bedrock_client is None:
        bedrock_client = BedrockAgentCoreClient()
    return bedrock_client

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Bedrock AgentCore API
    
    API Gateway event structure:
    {
        "httpMethod": "GET|POST",
        "path": "/invoke",
        "headers": {...},
        "body": "..." (JSON string)
    }
    """
    try:
        # Parse API Gateway event
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        headers = event.get('headers', {})
        body = event.get('body', '{}')
        
        # Parse body if it's a string
        if isinstance(body, str):
            try:
                body = json.loads(body) if body else {}
            except json.JSONDecodeError:
                body = {}
        
        # Route requests
        if path == '/health' or path == '/':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'Bedrock AgentCore API',
                    'agent_id': get_client().agent_id
                })
            }
        
        elif path == '/status':
            client = get_client()
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'running',
                    'agent_id': client.agent_id,
                    'region': client.region,
                    'agent_runtime_arn': client.agent_runtime_arn
                })
            }
        
        elif path == '/invoke' and http_method == 'POST':
            # Extract input
            input_text = (
                body.get('inputText') or 
                body.get('input') or 
                body.get('message') or 
                body.get('text') or
                str(body)
            )
            
            session_id = body.get('sessionId') or body.get('session_id')
            
            if not input_text:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'inputText is required'
                    })
                }
            
            # Invoke agent
            logger.info(f"Invoking agent with input: {input_text[:100]}...")
            result = get_client().invoke(
                input_text=input_text,
                session_id=session_id
            )
            
            if result['success']:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': True,
                        'completion': result['response'].get('completion', ''),
                        'session_id': result.get('session_id')
                    })
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    })
                }
        
        elif path == '/webhook' and http_method == 'POST':
            # Flexible webhook endpoint
            input_text = (
                body.get('inputText') or 
                body.get('input') or 
                body.get('message') or 
                body.get('text') or 
                body.get('prompt') or
                str(body)
            )
            
            session_id = body.get('sessionId') or body.get('session_id')
            
            result = get_client().invoke(
                input_text=input_text,
                session_id=session_id
            )
            
            status_code = 200 if result['success'] else 500
            return {
                'statusCode': status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': result['success'],
                    'response': result['response'].get('completion', '') if result['success'] else None,
                    'error': result.get('error') if not result['success'] else None,
                    'session_id': result.get('session_id')
                })
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'Path {path} not found'
                })
            }
    
    except Exception as e:
        logger.error(f"Error in Lambda handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

