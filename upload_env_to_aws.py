"""
Script to upload environment variables from .env file to AWS Systems Manager Parameter Store
Run this script to configure environment variables for AWS Bedrock Agent Core
"""
import os
import boto3
from dotenv import load_dotenv
import sys

# Load .env file
load_dotenv()

# AWS Configuration
REGION = 'us-west-2'
PARAMETER_PREFIX = '/bedrock-agentcore/RitvikAgent'

# Environment variables to upload
ENV_VARS = {
    'SUPABASE_URL': 'String',
    'SUPABASE_KEY': 'SecureString',
    'DDMAC_ANALYTICS_SUPABASE_URL': 'String',
    'DDMAC_ANALYTICS_SUPABASE_KEY': 'SecureString',
    'OPENAI_API_KEY': 'SecureString',
    'COMPOSIO_API_KEY': 'SecureString',
    'ZAPIER_WHATSAPP_WEBHOOK': 'String',
    'PERPLEXITY_API_KEY': 'SecureString',
    'EMAIL_ADDRESS': 'String',
    'EMAIL_PASSWORD': 'SecureString',
    'IMAP_SERVER': 'String',
    'IMAP_PORT': 'String',
    'WHATSAPP_PHONE_NUMBER_ID': 'String',
    'WHATSAPP_ACCESS_TOKEN': 'SecureString',
    'WEBHOOK_VERIFY_TOKEN': 'String',
    'DB_CONNECTION': 'String'
}

def upload_env_vars():
    """Upload environment variables to AWS Systems Manager Parameter Store"""
    ssm_client = boto3.client('ssm', region_name=REGION)
    
    uploaded = []
    skipped = []
    errors = []
    
    print(f"Uploading environment variables to AWS Parameter Store...")
    print(f"Region: {REGION}")
    print(f"Prefix: {PARAMETER_PREFIX}\n")
    
    for var_name, param_type in ENV_VARS.items():
        value = os.getenv(var_name)
        param_name = f"{PARAMETER_PREFIX}/{var_name}"
        
        if not value:
            skipped.append(var_name)
            print(f"⚠️  Skipping {var_name} (not found in .env file)")
            continue
        
        try:
            # Check if parameter already exists
            try:
                ssm_client.get_parameter(Name=param_name)
                # Parameter exists, update it
                ssm_client.put_parameter(
                    Name=param_name,
                    Value=value,
                    Type=param_type,
                    Overwrite=True
                )
                print(f"✅ Updated {var_name}")
            except ssm_client.exceptions.ParameterNotFound:
                # Parameter doesn't exist, create it
                ssm_client.put_parameter(
                    Name=param_name,
                    Value=value,
                    Type=param_type
                )
                print(f"✅ Created {var_name}")
            
            uploaded.append(var_name)
        except Exception as e:
            errors.append((var_name, str(e)))
            print(f"❌ Error uploading {var_name}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  ✅ Uploaded: {len(uploaded)}")
    print(f"  ⚠️  Skipped: {len(skipped)}")
    print(f"  ❌ Errors: {len(errors)}")
    print(f"{'='*60}")
    
    if uploaded:
        print(f"\n✅ Successfully uploaded {len(uploaded)} environment variables!")
        print(f"Your AWS Bedrock Agent Core agent can now access these variables.")
    
    if errors:
        print(f"\n❌ Errors occurred while uploading some variables:")
        for var_name, error in errors:
            print(f"  - {var_name}: {error}")

if __name__ == "__main__":
    try:
        upload_env_vars()
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)


