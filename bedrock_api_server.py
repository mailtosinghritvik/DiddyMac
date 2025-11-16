"""
REST API Server for Bedrock AgentCore
Exposes HTTP endpoints to access the Bedrock AgentCore agent
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import the Bedrock AgentCore client
from utils.bedrock_agentcore_client import BedrockAgentCoreClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Bedrock AgentCore API",
    description="REST API for accessing Bedrock AgentCore agent",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Bedrock client
bedrock_client = BedrockAgentCoreClient()

# Optional API Key authentication (set via environment variable)
API_KEY = os.getenv('API_KEY', None)

# Request/Response Models
class InvokeRequest(BaseModel):
    """Request model for invoking the agent"""
    input_text: str = Field(..., description="Input text to send to the agent", alias="inputText")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation context", alias="sessionId")
    
    class Config:
        populate_by_name = True

class CustomInvokeRequest(BaseModel):
    """Custom request format matching your agent.py"""
    prompt: str = Field(..., description="User's prompt/input")
    user: Optional[str] = Field("api@example.com", description="User identifier")
    source: Optional[str] = Field("api", description="Source of the request")
    subject: Optional[str] = Field(None, description="Optional subject line")
    phone_number: Optional[str] = Field(None, description="Optional phone number", alias="phone_number")
    session_id: Optional[str] = Field(None, description="Optional session ID", alias="sessionId")
    
    class Config:
        populate_by_name = True

class InvokeResponse(BaseModel):
    """Response model"""
    success: bool
    completion: Optional[str] = None
    session_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: str

# Authentication dependency (optional)
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key if configured"""
    if API_KEY:
        if not x_api_key or x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Bedrock AgentCore API",
        "version": "1.0.0",
        "status": "running",
        "agent_id": bedrock_client.agent_id,
        "endpoints": {
            "/invoke": "POST - Invoke agent with inputText",
            "/invoke/custom": "POST - Invoke agent with custom format",
            "/health": "GET - Health check",
            "/status": "GET - API status"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/status")
async def status():
    """Detailed status endpoint"""
    return {
        "status": "running",
        "agent_id": bedrock_client.agent_id,
        "region": bedrock_client.region,
        "agent_runtime_arn": bedrock_client.agent_runtime_arn,
        "timestamp": datetime.now().isoformat()
    }

# Main invoke endpoint
@app.post("/invoke", response_model=InvokeResponse)
async def invoke_agent(
    request: InvokeRequest,
    api_key_verified: bool = Depends(verify_api_key)
):
    """
    Invoke the Bedrock AgentCore agent
    
    Request body:
    ```json
    {
        "inputText": "Hello, how are you?",
        "sessionId": "optional-session-id"
    }
    ```
    """
    try:
        logger.info(f"Invoke request received: {request.input_text[:100]}...")
        
        result = bedrock_client.invoke(
            input_text=request.input_text,
            session_id=request.session_id
        )
        
        if result['success']:
            return InvokeResponse(
                success=True,
                completion=result['response'].get('completion', ''),
                session_id=result.get('session_id'),
                timestamp=datetime.now().isoformat()
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Unknown error')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Custom format endpoint
@app.post("/invoke/custom", response_model=InvokeResponse)
async def invoke_agent_custom(
    request: CustomInvokeRequest,
    api_key_verified: bool = Depends(verify_api_key)
):
    """
    Invoke agent with custom format (matches your agent.py format)
    
    Request body:
    ```json
    {
        "prompt": "Schedule a meeting tomorrow at 3pm",
        "user": "user@example.com",
        "source": "api",
        "subject": "Meeting Request",
        "phone_number": "+1234567890",
        "sessionId": "optional-session-id"
    }
    ```
    """
    try:
        logger.info(f"Custom invoke request received: {request.prompt[:100]}...")
        
        result = bedrock_client.invoke_custom_format(
            prompt=request.prompt,
            user=request.user,
            source=request.source,
            subject=request.subject,
            phone_number=request.phone_number,
            session_id=request.session_id
        )
        
        if result['success']:
            return InvokeResponse(
                success=True,
                completion=result['response'].get('completion', ''),
                session_id=result.get('session_id'),
                timestamp=datetime.now().isoformat()
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Unknown error')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Alternative: Simple POST endpoint (for webhooks)
@app.post("/webhook")
async def webhook_endpoint(
    request: Request,
    api_key_verified: bool = Depends(verify_api_key)
):
    """
    Webhook endpoint - accepts any JSON format and tries to extract input
    """
    try:
        body = await request.json()
        
        # Try to extract input from various formats
        input_text = (
            body.get('inputText') or 
            body.get('input') or 
            body.get('message') or 
            body.get('text') or 
            body.get('prompt') or
            str(body)
        )
        
        session_id = body.get('sessionId') or body.get('session_id')
        
        logger.info(f"Webhook request received: {input_text[:100]}...")
        
        result = bedrock_client.invoke(
            input_text=input_text,
            session_id=session_id
        )
        
        if result['success']:
            return {
                "success": True,
                "response": result['response'].get('completion', ''),
                "session_id": result.get('session_id'),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": result.get('error', 'Unknown error'),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

# Start server
def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server"""
    logger.info(f"Starting Bedrock AgentCore API server on {host}:{port}")
    logger.info(f"Agent ID: {bedrock_client.agent_id}")
    logger.info(f"Region: {bedrock_client.region}")
    
    if API_KEY:
        logger.info("API key authentication enabled")
    else:
        logger.warning("API key authentication disabled - set API_KEY environment variable")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    start_server(port=port)

