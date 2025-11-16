"""
Utility to load environment variables from AWS Systems Manager Parameter Store
for AWS Bedrock Agent Core runtime
"""
import os
import boto3
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def load_env_from_aws_ssm(parameter_prefix: str = "/bedrock-agentcore/RitvikAgent") -> None:
    """
    Load environment variables from AWS Systems Manager Parameter Store
    
    Args:
        parameter_prefix: Prefix for parameter names (e.g., /bedrock-agentcore/RitvikAgent)
    """
    try:
        ssm_client = boto3.client('ssm', region_name=os.getenv('AWS_REGION', 'us-west-2'))
        
        # List of environment variables to load
        env_vars = [
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'DDMAC_ANALYTICS_SUPABASE_URL',
            'DDMAC_ANALYTICS_SUPABASE_KEY',
            'OPENAI_API_KEY',
            'COMPOSIO_API_KEY',
            'ZAPIER_WHATSAPP_WEBHOOK',
            'PERPLEXITY_API_KEY',
            'EMAIL_ADDRESS',
            'EMAIL_PASSWORD',
            'IMAP_SERVER',
            'IMAP_PORT',
            'WHATSAPP_PHONE_NUMBER_ID',
            'WHATSAPP_ACCESS_TOKEN',
            'WEBHOOK_VERIFY_TOKEN',
            'DB_CONNECTION'
        ]
        
        loaded_count = 0
        for var_name in env_vars:
            # Skip if already set
            if os.getenv(var_name):
                continue
            
            # Try to get from Parameter Store
            param_name = f"{parameter_prefix}/{var_name}"
            try:
                response = ssm_client.get_parameter(
                    Name=param_name,
                    WithDecryption=True  # Decrypt SecureString parameters
                )
                os.environ[var_name] = response['Parameter']['Value']
                loaded_count += 1
                logger.info(f"Loaded {var_name} from AWS Parameter Store")
            except ssm_client.exceptions.ParameterNotFound:
                logger.debug(f"Parameter {param_name} not found in Parameter Store")
                continue
            except Exception as e:
                logger.warning(f"Error loading {param_name} from Parameter Store: {str(e)}")
                continue
        
        if loaded_count > 0:
            logger.info(f"Loaded {loaded_count} environment variables from AWS Parameter Store")
        else:
            logger.info("No environment variables loaded from AWS Parameter Store (using existing env vars or defaults)")
            
    except Exception as e:
        logger.warning(f"Could not load environment variables from AWS Parameter Store: {str(e)}")
        logger.info("Continuing with existing environment variables...")


def ensure_env_vars_loaded():
    """
    Ensure environment variables are loaded - tries dotenv first, then AWS Parameter Store
    """
    from dotenv import load_dotenv
    
    # First try loading from .env file (for local development)
    load_dotenv()
    
    # Then try loading from AWS Parameter Store (for AWS Bedrock Agent Core)
    # Only if we're running in AWS (check for AWS-specific environment variables)
    if os.getenv('AWS_EXECUTION_ENV') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('DOCKER_CONTAINER'):
        load_env_from_aws_ssm()


