"""
AWS Bedrock Agent Core Entry Point
FastAPI application wrapper for DiddyMac multi-agent system
"""
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from AWS Parameter Store (for AWS Bedrock Agent Core)
# This must happen before any other imports that need env vars
try:
    from utils.aws_env_loader import ensure_env_vars_loaded
    ensure_env_vars_loaded()
    logger.info("Environment variables loaded (from .env or AWS Parameter Store)")
except Exception as e:
    logger.warning(f"Could not load environment variables: {str(e)}")

# Lazy import to avoid startup errors
# from main import process_request_async


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Application starting up...")
    logger.info("Health check endpoints available at: /, /ping, /health")
    yield
    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title="DiddyMac Agent",
    description="Multi-agent communication system for email and WhatsApp",
    version="1.0.0",
    lifespan=lifespan
)


# Global exception handler to catch any unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure we always return JSON responses"""
    import traceback
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=200,  # Return 200 with error in body for AWS compatibility
        content={
            "status": "error",
            "type": None,
            "message": None,
            "final_output": None,
            "error": str(exc),
            "error_type": type(exc).__name__
        }
    )


class AgentRequest(BaseModel):
    """Request model for agent processing"""
    id: Optional[int] = None
    created_at: Optional[str] = None
    user: str
    source: str
    input: str
    subject: Optional[str] = None
    phone_number: Optional[str] = None


class AgentResponse(BaseModel):
    """Response model for agent processing"""
    status: str
    type: Optional[str] = None
    message: Optional[str] = None
    final_output: Optional[str] = None
    error: Optional[str] = None
    output_dir: Optional[str] = None


@app.get("/")
def root(response: Response):
    """
    Health check endpoint - AWS Bedrock Agent Core requirement
    Must return HTTP 200 with simple JSON response immediately
    """
    logger.info("Health check requested at GET /")
    response.status_code = 200
    return {"status": "ok"}


@app.get("/ping")
def ping(response: Response):
    """
    AWS Bedrock Agent Core health check endpoint - primary
    Must return HTTP 200 with simple JSON response immediately
    """
    logger.info("Health check requested at GET /ping")
    response.status_code = 200
    return {"status": "ok"}


@app.get("/health")
def health(response: Response):
    """
    Health check endpoint - alternative
    Must return HTTP 200 with simple JSON response immediately
    """
    logger.info("Health check requested at GET /health")
    response.status_code = 200
    return {"status": "ok"}


# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging"""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")
    return response


# @app.post("/invocations")
# async def invocations_endpoint(request: Request):
#     """
#     AWS Bedrock Agent Core invocations endpoint - PRIMARY ENDPOINT
#     This is the endpoint AWS Bedrock Agent Core calls for agent invocations
#     """
#     logger.info("POST request received at /invocations (AWS Bedrock Agent Core endpoint)")
#     # Delegate to invoke handler
#     return await invoke_agent(request)


# @app.post("/")
# async def root_post(request: Request):
#     """
#     Root POST endpoint - Alternative endpoint
#     """
#     logger.info("POST request received at root /")
#     # Delegate to invoke endpoint
#     return await invoke_agent(request)


@app.post("/invoke")
async def invoke_agent(request: Request):
    """
    Main endpoint for processing agent requests from AWS Bedrock Agent Core
    
    This endpoint accepts requests in various formats and processes them
    through the DiddyMac multi-agent pipeline.
    """
    try:
        # Lazy import to avoid startup errors
        from main import process_request_async
        
        # Get request body with error handling
        try:
            body = await request.json()
        except Exception as json_error:
            logger.error(f"Error parsing JSON request: {str(json_error)}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "type": None,
                    "message": None,
                    "final_output": None,
                    "error": f"Invalid JSON in request: {str(json_error)}"
                }
            )
        
        # Handle different request formats
        # Format 1: Direct JSON with user, source, input, etc.
        if "user" in body and "input" in body:
            json_input = {
                "id": body.get("id"),
                "created_at": body.get("created_at") or datetime.now().isoformat(),
                "user": body.get("user"),
                "source": body.get("source", "email"),
                "input": body.get("input"),
                "subject": body.get("subject"),
                "phone_number": body.get("phone_number")
            }
        # Format 2: AWS Bedrock Agent Core format with prompt
        elif "prompt" in body:
            json_input = {
                "id": body.get("id"),
                "created_at": datetime.now().isoformat(),
                "user": body.get("user", "user@example.com"),
                "source": body.get("source", "email"),
                "input": body.get("prompt"),
                "subject": body.get("subject"),
                "phone_number": body.get("phone_number")
            }
        # Format 3: Already in correct format
        else:
            json_input = body
        
        # Process the request
        result = await process_request_async(json_input)
        
        # Return the result as JSON
        return JSONResponse(content={
            "status": result.get("status", "unknown"),
            "type": result.get("type"),
            "message": result.get("message"),
            "final_output": result.get("final_output"),
            "error": result.get("error"),
            "output_dir": result.get("output_dir")
        })
    
    except Exception as e:
        import traceback
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        error_detail = {
            "status": "error",
            "type": None,
            "message": None,
            "final_output": None,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        # Return JSON response instead of raising HTTPException
        # AWS Bedrock Agent Core expects a JSON response, not an HTTP exception
        return JSONResponse(
            status_code=200,  # Return 200 with error in body for AWS compatibility
            content=error_detail
        )


# @app.post("/process")
# async def process_request_endpoint(request: Request):
#     """
#     Alternative endpoint that accepts raw JSON
#     """
#     try:
#         # Lazy import to avoid startup errors
#         from main import process_request_async
        
#         json_data = await request.json()
#         result = await process_request_async(json_data)
#         return JSONResponse(content=result)
#     except Exception as e:
#         logger.error(f"Error processing request: {str(e)}", exc_info=True)
#         return JSONResponse(
#             status_code=200,
#             content={
#                 "status": "error",
#                 "type": None,
#                 "message": None,
#                 "final_output": None,
#                 "error": str(e)
#             }
#         )


# Start server - AWS Bedrock Agent Core runs: opentelemetry-instrument python -m agent
# AWS Bedrock Agent Core HTTP protocol REQUIRES port 8080 (not 8000!)
def start_server():
    """Start the FastAPI server on the correct port for AWS Bedrock Agent Core"""
    # AWS Bedrock Agent Core HTTP protocol REQUIRES port 8080
    # This is a mandatory requirement for AgentCore Runtime
    port = int(os.getenv("PORT", os.getenv("BEDROCK_AGENTCORE_PORT", "8080")))
    
    logger.info(f"Starting FastAPI server on 0.0.0.0:{port} (AWS Bedrock Agent Core HTTP requires port 8080)")
    logger.info(f"Health check endpoints: http://0.0.0.0:{port}/, http://0.0.0.0:{port}/ping, http://0.0.0.0:{port}/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Must bind to 0.0.0.0 for AWS Bedrock Agent Core
        port=8080,
        log_level="info",
        access_log=True,
        loop="asyncio"
    )

# Start server when module is executed
# AWS Bedrock Agent Core runs: opentelemetry-instrument python -m agent
if __name__ == "__main__" or __name__ == "__mp_main__":
    # Direct execution: python agent.py
    # This will also catch AWS Bedrock Agent Core execution: python -m agent
    start_server()

