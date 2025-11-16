"""
Webhook Proxy Server for Bedrock AgentCore
This creates a simple webhook endpoint that forwards requests to Bedrock AgentCore
Deploy this on Railway, Heroku, or any cloud service to use as webhook URL
"""
import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for webhook services

# Configuration from environment variables
AGENT_ID = os.getenv('BEDROCK_AGENT_ID', 'RitvikAgent-Nfl5014O49')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')

# Initialize Bedrock client
bedrock_client = boto3.client('bedrock-agentcore', region_name=AWS_REGION)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'agent_id': AGENT_ID}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Main webhook endpoint
    Accepts webhook requests and forwards to Bedrock AgentCore
    """
    try:
        # Get request data
        if request.is_json:
            data = request.json
        else:
            # Try to parse as form data
            data = request.form.to_dict()
            # Try to parse JSON from form data
            if 'payload' in data:
                try:
                    data = json.loads(data['payload'])
                except:
                    pass
        
        logger.info(f"Received webhook request: {data}")
        
        # Extract input text from various formats
        input_text = None
        
        # Format 1: Direct inputText
        if 'inputText' in data:
            input_text = data['inputText']
        
        # Format 2: Custom format (prompt)
        elif 'prompt' in data:
            input_text = data['prompt']
        
        # Format 3: Common webhook formats
        elif 'message' in data:
            input_text = data['message']
        elif 'text' in data:
            input_text = data['text']
        elif 'input' in data:
            input_text = data['input']
        elif 'body' in data:
            input_text = data['body']
        
        # Format 4: Convert entire payload to string
        else:
            input_text = json.dumps(data) if isinstance(data, dict) else str(data)
        
        if not input_text:
            return jsonify({
                'success': False,
                'error': 'No input text found in webhook payload'
            }), 400
        
        # Get optional session ID
        session_id = data.get('sessionId') or data.get('session_id')
        
        # Call Bedrock AgentCore
        logger.info(f"Invoking Bedrock AgentCore with input: {input_text[:100]}...")
        
        invoke_params = {
            'agentId': AGENT_ID,
            'inputText': input_text
        }
        
        if session_id:
            invoke_params['sessionId'] = session_id
        
        response = bedrock_client.invoke_agent(**invoke_params)
        
        # Extract completion from response
        completion = response.get('completion', '')
        
        logger.info(f"Bedrock AgentCore response received: {len(completion)} characters")
        
        # Return response
        return jsonify({
            'success': True,
            'response': completion,
            'session_id': response.get('sessionId'),
            'stop_reason': response.get('stopReason')
        }), 200
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"AWS ClientError: {error_code} - {error_message}")
        return jsonify({
            'success': False,
            'error': error_message,
            'error_code': error_code
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/webhook/custom', methods=['POST'])
def webhook_custom():
    """
    Custom format webhook endpoint
    Matches your agent.py custom format
    """
    try:
        data = request.json if request.is_json else request.form.to_dict()
        
        # Extract fields for custom format
        prompt = data.get('prompt') or data.get('message') or data.get('input')
        user = data.get('user', 'webhook@example.com')
        source = data.get('source', 'webhook')
        subject = data.get('subject')
        phone_number = data.get('phone_number')
        
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'prompt, message, or input is required'
            }), 400
        
        # Format input text
        input_text = prompt
        if subject:
            input_text = f"Subject: {subject}\n\n{prompt}"
        
        # Call Bedrock AgentCore
        response = bedrock_client.invoke_agent(
            agentId=AGENT_ID,
            inputText=input_text
        )
        
        return jsonify({
            'success': True,
            'response': response.get('completion', ''),
            'session_id': response.get('sessionId')
        }), 200
        
    except Exception as e:
        logger.error(f"Error in custom webhook: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/', methods=['GET', 'POST'])
def root():
    """Root endpoint with usage information"""
    if request.method == 'POST':
        # Forward to webhook endpoint
        return webhook()
    
    return jsonify({
        'service': 'Bedrock AgentCore Webhook Proxy',
        'agent_id': AGENT_ID,
        'region': AWS_REGION,
        'endpoints': {
            '/webhook': 'Standard webhook endpoint',
            '/webhook/custom': 'Custom format webhook endpoint',
            '/health': 'Health check'
        },
        'usage': {
            'method': 'POST',
            'content_type': 'application/json',
            'body': {
                'inputText': 'Your message here',
                'sessionId': 'optional-session-id'
            }
        }
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting webhook proxy server on port {port}")
    logger.info(f"Agent ID: {AGENT_ID}")
    logger.info(f"Region: {AWS_REGION}")
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'False').lower() == 'true')

