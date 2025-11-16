#!/bin/bash
# Start the Bedrock AgentCore API server

echo "Starting Bedrock AgentCore API Server..."
echo "========================================"
echo ""

# Check if port is already in use
PORT=${PORT:-8000}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port $PORT is already in use"
    echo "Using port 8001 instead..."
    PORT=8001
fi

echo "Server will start on: http://localhost:$PORT"
echo ""
echo "API Endpoints:"
echo "  GET  http://localhost:$PORT/health"
echo "  GET  http://localhost:$PORT/status"
echo "  POST http://localhost:$PORT/invoke"
echo "  POST http://localhost:$PORT/invoke/custom"
echo "  POST http://localhost:$PORT/webhook"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python bedrock_api_server.py

