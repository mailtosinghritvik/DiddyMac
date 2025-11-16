"""
AWS Lambda function to access Bedrock AgentCore Agent
Self-contained Lambda handler with embedded Bedrock client
"""
import json
import logging
import os
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Embedded Bedrock AgentCore Client (no external dependencies)
class BedrockAgentCoreClient:
    """Bedrock AgentCore client embedded in Lambda function"""
    
    def __init__(
        self,
        agent_id: str = "RitvikAgent-Nfl5014O49",
        agent_runtime_arn: Optional[str] = None,
        region: str = "us-west-2",
        account_id: str = "624571284647"
    ):
        self.agent_id = agent_id
        self.region = region
        self.account_id = account_id
        
        if agent_runtime_arn:
            self.agent_runtime_arn = agent_runtime_arn
        else:
            self.agent_runtime_arn = f"arn:aws:bedrock-agentcore:{region}:{account_id}:runtime/{agent_id}"
        
        self.client = boto3.client('bedrock-agentcore', region_name=region)
        logger.info(f"Initialized Bedrock client for agent: {agent_id}")
    
    def invoke(
        self,
        input_text: str,
        session_id: Optional[str] = None,
        user: Optional[str] = None,
        source: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invoke the Bedrock AgentCore agent"""
        try:
            logger.info(f"Invoking agent {self.agent_id} with input: {input_text[:100]}...")
            
            # Prepare payload with all required fields for the agent
            # The agent expects: user, source, input (or prompt), subject
            payload = {
                'prompt': input_text,  # Use 'prompt' so agent.py Format 2 handles it correctly
                'user': user or 'lambda@example.com',  # Default user if not provided
                'source': source or 'lambda',  # Default source if not provided
                'subject': subject  # Optional subject
            }
            
            # Prepare invocation parameters
            invoke_params = {
                'agentRuntimeArn': self.agent_runtime_arn,
                'payload': json.dumps(payload),
                'contentType': 'application/json',
                'accept': 'application/json'
            }
            
            if session_id:
                invoke_params['runtimeSessionId'] = session_id
                logger.debug(f"Using session ID: {session_id}")
            
            # Invoke the agent
            response = self.client.invoke_agent_runtime(**invoke_params)
            
            # Parse response payload
            response_body = response.get('response')
            if hasattr(response_body, 'read'):
                response_payload = response_body.read()
                if isinstance(response_payload, bytes):
                    response_payload = response_payload.decode('utf-8')
            else:
                response_payload = response.get('payload', b'')
                if isinstance(response_payload, bytes):
                    response_payload = response_payload.decode('utf-8')
            
            try:
                parsed_payload = json.loads(response_payload) if response_payload else {}
            except (json.JSONDecodeError, TypeError):
                parsed_payload = {'text': response_payload} if response_payload else {}
            
            # Extract completion
            completion = (
                parsed_payload.get('completion') or 
                parsed_payload.get('text') or 
                parsed_payload.get('output') or 
                parsed_payload.get('message') or 
                str(parsed_payload) if parsed_payload else ''
            )
            
            return {
                'success': True,
                'agent_id': self.agent_id,
                'session_id': response.get('runtimeSessionId') or session_id,
                'response': {
                    'completion': completion,
                    'payload': parsed_payload,
                    'raw': response
                }
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"AWS ClientError: {error_code} - {error_message}")
            return {
                'success': False,
                'error': error_message,
                'error_code': error_code,
                'agent_id': self.agent_id
            }
        except BotoCoreError as e:
            logger.error(f"BotoCoreError: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'BotoCoreError',
                'agent_id': self.agent_id
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'agent_id': self.agent_id
            }

# Initialize client (reused across invocations for performance)
_client = None

def get_client() -> BedrockAgentCoreClient:
    """Get or create Bedrock client (singleton pattern for Lambda)"""
    global _client
    if _client is None:
        # Allow override via environment variables
        agent_id = os.getenv('BEDROCK_AGENT_ID', 'RitvikAgent-Nfl5014O49')
        region = os.getenv('AWS_REGION', 'us-west-2')
        account_id = os.getenv('AWS_ACCOUNT_ID', '624571284647')
        
        _client = BedrockAgentCoreClient(
            agent_id=agent_id,
            region=region,
            account_id=account_id
        )
        logger.info(f"Initialized Bedrock client for agent: {agent_id}")
    
    return _client

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Bedrock AgentCore agent access
    
    Supports multiple event sources:
    1. API Gateway (REST/HTTP API)
    2. Function URL
    3. Direct invocation
    4. EventBridge/Scheduled events
    
    Event formats:
    
    API Gateway/Function URL:
    {
        "httpMethod": "POST",
        "path": "/invoke",
        "body": "{\"inputText\": \"Hello\"}"
    }
    
    Direct invocation:
    {
        "inputText": "Hello",
        "sessionId": "optional-session-id"
    }
    """
    try:
        # Determine event source type
        if 'httpMethod' in event or 'requestContext' in event:
            # API Gateway or Function URL event
            return handle_api_request(event)
        else:
            # Direct invocation or other event source
            return handle_direct_invocation(event)
    
    except Exception as e:
        logger.error(f"Error in Lambda handler: {str(e)}", exc_info=True)
        return create_error_response(str(e), 500)

def handle_api_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle API Gateway or Function URL requests"""
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    headers = event.get('headers', {})
    
    # Parse body
    body = event.get('body', '{}')
    if isinstance(body, str):
        try:
            body = json.loads(body) if body else {}
        except json.JSONDecodeError:
            body = {}
    
    # Route based on path and method
    if path == '/health' or (path == '/' and http_method == 'GET'):
        return create_success_response({
            'status': 'healthy',
            'service': 'Bedrock AgentCore Lambda',
            'agent_id': get_client().agent_id,
            'region': get_client().region
        })
    
    elif path == '/status' and http_method == 'GET':
        client = get_client()
        return create_success_response({
            'status': 'running',
            'agent_id': client.agent_id,
            'region': client.region,
            'agent_runtime_arn': client.agent_runtime_arn
        })
    
    elif path == '/invoke' and http_method == 'POST':
        # Ensure body has all required fields with defaults
        if 'user' not in body:
            body['user'] = body.get('user_email', 'lambda@example.com')
        if 'source' not in body:
            body['source'] = 'lambda'
        return handle_invoke_request(body)
    
    elif path == '/webhook' and http_method == 'POST':
        return handle_webhook_request(body)
    
    else:
        return create_error_response(f'Path {path} with method {http_method} not found', 404)

def handle_direct_invocation(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle direct Lambda invocation (not via API)"""
    input_text = event.get('inputText') or event.get('input') or event.get('message')
    session_id = event.get('sessionId') or event.get('session_id')
    
    # Extract user, source, subject fields
    user = event.get('user') or event.get('user_email') or 'lambda@example.com'
    source = event.get('source') or 'lambda'
    subject = event.get('subject')
    
    if not input_text:
        return create_error_response('inputText is required', 400)
    
    return handle_invoke_request({
        'inputText': input_text,
        'sessionId': session_id,
        'user': user,
        'source': source,
        'subject': subject
    })

def handle_invoke_request(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle agent invocation request"""
    # Extract input text
    input_text = (
        body.get('inputText') or 
        body.get('input') or 
        body.get('message') or 
        body.get('text') or
        body.get('prompt')
    )
    
    session_id = body.get('sessionId') or body.get('session_id')
    
    # Extract user, source, subject fields (required for database insertion)
    user = body.get('user') or body.get('user_email') or 'lambda@example.com'
    source = body.get('source') or 'lambda'
    subject = body.get('subject')
    
    if not input_text:
        return create_error_response('inputText, input, message, text, or prompt is required', 400)
    
    # Invoke agent with all required fields
    logger.info(f"Invoking agent with input: {input_text[:100]}...")
    logger.info(f"User: {user}, Source: {source}, Subject: {subject}")
    
    try:
        result = get_client().invoke(
            input_text=str(input_text),
            session_id=session_id,
            user=user,
            source=source,
            subject=subject
        )
        
        if result['success']:
            return create_success_response({
                'success': True,
                'completion': result['response'].get('completion', ''),
                'session_id': result.get('session_id'),
                'payload': result['response'].get('payload', {})
            })
        else:
            return create_error_response(
                result.get('error', 'Unknown error'),
                500
            )
    
    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}", exc_info=True)
        return create_error_response(f"Failed to invoke agent: {str(e)}", 500)

def handle_webhook_request(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle flexible webhook request"""
    # Try to extract input from various formats
    input_text = (
        body.get('inputText') or 
        body.get('input') or 
        body.get('message') or 
        body.get('text') or 
        body.get('prompt') or
        str(body) if body else None
    )
    
    session_id = body.get('sessionId') or body.get('session_id')
    
    # Extract user, source, subject fields
    user = body.get('user') or body.get('user_email') or 'webhook@example.com'
    source = body.get('source') or 'webhook'
    subject = body.get('subject')
    
    if not input_text:
        return create_error_response('No input text found in request body', 400)
    
    return handle_invoke_request({
        'inputText': input_text,
        'sessionId': session_id,
        'user': user,
        'source': source,
        'subject': subject
    })

def create_success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create successful API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(data, default=str)
    }

def create_error_response(error_message: str, status_code: int = 400) -> Dict[str, Any]:
    """Create error API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps({
            'success': False,
            'error': error_message
        }, default=str)
    }

# For testing locally
if __name__ == '__main__':
    # Test event
    test_event = {
        'httpMethod': 'POST',
        'path': '/invoke',
        'body': json.dumps({
            'inputText': 'Hello, this is a test'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2, default=str))
