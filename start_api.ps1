# PowerShell script to start the Bedrock AgentCore API server

Write-Host "Starting Bedrock AgentCore API Server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if port is specified
$port = if ($env:PORT) { $env:PORT } else { "8000" }

Write-Host "Server will start on: http://localhost:$port" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Endpoints:" -ForegroundColor Yellow
Write-Host "  GET  http://localhost:$port/health"
Write-Host "  GET  http://localhost:$port/status"
Write-Host "  POST http://localhost:$port/invoke"
Write-Host "  POST http://localhost:$port/invoke/custom"
Write-Host "  POST http://localhost:$port/webhook"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python bedrock_api_server.py

