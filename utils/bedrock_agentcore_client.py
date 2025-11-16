"""
Bedrock AgentCore API Client
Utility module for calling Bedrock AgentCore agent from Python
"""
import boto3
import json
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class BedrockAgentCoreClient:
    """
    Client for invoking Bedrock AgentCore agents
    """
    
    def __init__(
        self,
        agent_id: str = "RitvikAgent-Nfl5014O49",
        agent_runtime_arn: Optional[str] = None,
        region: str = "us-west-2",
        account_id: str = "624571284647",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None
    ):
        """
        Initialize Bedrock AgentCore client
        
        Args:
            agent_id: Bedrock AgentCore agent ID
            agent_runtime_arn: Full agent runtime ARN (auto-constructed if not provided)
            region: AWS region
            account_id: AWS account ID
            aws_access_key_id: Optional AWS access key (uses default credentials if not provided)
            aws_secret_access_key: Optional AWS secret key
            aws_session_token: Optional AWS session token (for temporary credentials)
        """
        self.agent_id = agent_id
        self.region = region
        self.account_id = account_id
        
        # Construct agent runtime ARN if not provided
        if agent_runtime_arn:
            self.agent_runtime_arn = agent_runtime_arn
        else:
            self.agent_runtime_arn = f"arn:aws:bedrock-agentcore:{region}:{account_id}:runtime/{agent_id}"
        
        # Initialize boto3 client
        client_kwargs = {'region_name': region}
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs.update({
                'aws_access_key_id': aws_access_key_id,
                'aws_secret_access_key': aws_secret_access_key
            })
            if aws_session_token:
                client_kwargs['aws_session_token'] = aws_session_token
        
        self.client = boto3.client('bedrock-agentcore', **client_kwargs)
        logger.info(f"Initialized Bedrock AgentCore client for agent: {agent_id} in region: {region}")
    
    def invoke(
        self,
        input_text: str,
        session_id: Optional[str] = None,
        enable_trace: bool = False
    ) -> Dict[str, Any]:
        """
        Invoke the Bedrock AgentCore agent
        
        Args:
            input_text: Text input to send to the agent
            session_id: Optional session ID for maintaining conversation context
            enable_trace: Whether to include trace information in response
        
        Returns:
            dict: Response from the agent containing completion and metadata
        
        Raises:
            ClientError: If AWS service returns an error
            BotoCoreError: If there's an issue with AWS SDK
        """
        try:
            logger.info(f"Invoking agent {self.agent_id} with input: {input_text[:100]}...")
            
            # Prepare payload for invoke_agent_runtime
            # The payload should contain the input text
            payload = {
                'inputText': input_text
            }
            
            # Prepare invocation parameters for invoke_agent_runtime
            invoke_params = {
                'agentRuntimeArn': self.agent_runtime_arn,
                'payload': json.dumps(payload),
                'contentType': 'application/json',
                'accept': 'application/json'
            }
            
            if session_id:
                invoke_params['runtimeSessionId'] = session_id
                logger.debug(f"Using session ID: {session_id}")
            
            # Invoke the agent (using invoke_agent_runtime for Bedrock AgentCore)
            response = self.client.invoke_agent_runtime(**invoke_params)
            
            # Parse response payload
            # The response contains a 'response' field (StreamingBody) that needs to be read
            response_body = response.get('response')
            if hasattr(response_body, 'read'):
                # It's a StreamingBody, read it
                response_payload = response_body.read()
                if isinstance(response_payload, bytes):
                    response_payload = response_payload.decode('utf-8')
            else:
                # Try payload field
                response_payload = response.get('payload', b'')
                if isinstance(response_payload, bytes):
                    response_payload = response_payload.decode('utf-8')
            
            try:
                parsed_payload = json.loads(response_payload) if response_payload else {}
            except (json.JSONDecodeError, TypeError):
                parsed_payload = {'text': response_payload} if response_payload else {}
            
            # Extract completion from parsed payload
            completion = parsed_payload.get('completion') or parsed_payload.get('text') or parsed_payload.get('output') or parsed_payload.get('message') or str(parsed_payload) if parsed_payload else ''
            
            # Return response
            result = {
                'success': True,
                'agent_id': self.agent_id,
                'session_id': response.get('runtimeSessionId') or session_id,
                'response': {
                    'completion': completion,
                    'payload': parsed_payload,
                    'raw': response
                }
            }
            
            logger.info(f"Successfully invoked agent {self.agent_id}")
            return result
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"AWS ClientError invoking agent: {error_code} - {error_message}")
            return {
                'success': False,
                'error': error_message,
                'error_code': error_code,
                'agent_id': self.agent_id
            }
        except BotoCoreError as e:
            logger.error(f"BotoCoreError invoking agent: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'BotoCoreError',
                'agent_id': self.agent_id
            }
        except Exception as e:
            logger.error(f"Unexpected error invoking agent: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'agent_id': self.agent_id
            }
    
    def invoke_custom_format(
        self,
        prompt: str,
        user: str = "user@example.com",
        source: str = "api",
        subject: Optional[str] = None,
        phone_number: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke agent with custom format matching your agent.py implementation
        
        Args:
            prompt: The user's prompt/input
            user: User identifier
            source: Source of the request (e.g., "email", "api", "whatsapp")
            subject: Optional subject line
            phone_number: Optional phone number
            session_id: Optional session ID for conversation context
        
        Returns:
            dict: Response from the agent
        """
        # Format the input text to include context
        input_text = prompt
        if subject:
            input_text = f"Subject: {subject}\n\n{prompt}"
        
        return self.invoke(input_text=input_text, session_id=session_id)


# Convenience function for quick usage
def invoke_bedrock_agent(
    input_text: str,
    agent_id: str = "RitvikAgent-Nfl5014O49",
    region: str = "us-west-2",
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to quickly invoke a Bedrock AgentCore agent
    
    Args:
        input_text: Text to send to the agent
        agent_id: Agent ID (default: RitvikAgent-Nfl5014O49)
        region: AWS region (default: us-west-2)
        session_id: Optional session ID for conversation context
    
    Returns:
        dict: Response from the agent
    
    Example:
        >>> result = invoke_bedrock_agent("Hello, how are you?")
        >>> print(result['response']['completion'])
    """
    client = BedrockAgentCoreClient(agent_id=agent_id, region=region)
    return client.invoke(input_text=input_text, session_id=session_id)


if __name__ == '__main__':
    # Example usage
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Get input from command line or use default
    input_text = sys.argv[1] if len(sys.argv) > 1 else "Hello, how are you?"
    
    # Create client and invoke
    client = BedrockAgentCoreClient()
    result = client.invoke(input_text=input_text)
    
    # Print result
    print(json.dumps(result, indent=2, default=str))

