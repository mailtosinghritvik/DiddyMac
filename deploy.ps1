# PowerShell Deployment script for Bedrock AgentCore Agent
# Usage: .\deploy.ps1 [command]

param(
    [Parameter(Position=0)]
    [string]$Action = "deploy",
    
    [Parameter(Position=1)]
    [string]$TestMessage = "Hello, how are you?"
)

# Configuration
$AGENT_NAME = "RitvikAgent"
$REGION = "us-west-2"
$AGENT_ID = "RitvikAgent-Nfl5014O49"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Bedrock AgentCore Deployment Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

# Check prerequisites
Write-Status "Checking prerequisites..."

# Check if agentcore CLI is installed
try {
    $null = Get-Command agentcore -ErrorAction Stop
    Write-Status "✓ agentcore CLI found"
} catch {
    Write-Error "bedrock-agentcore-starter-toolkit is not installed"
    Write-Host "Install it with: pip install bedrock-agentcore-starter-toolkit"
    exit 1
}

# Check if AWS CLI is installed
try {
    $null = Get-Command aws -ErrorAction Stop
    Write-Status "✓ AWS CLI found"
} catch {
    Write-Error "AWS CLI is not installed"
    Write-Host "Install it from: https://aws.amazon.com/cli/"
    exit 1
}

# Check AWS credentials
try {
    $null = aws sts get-caller-identity 2>&1
    Write-Status "✓ AWS credentials configured"
} catch {
    Write-Error "AWS credentials not configured"
    Write-Host "Run: aws configure"
    exit 1
}

# Check if .bedrock_agentcore.yaml exists
if (-not (Test-Path ".bedrock_agentcore.yaml")) {
    Write-Error ".bedrock_agentcore.yaml not found"
    exit 1
}
Write-Status "✓ Configuration file found"

Write-Host ""

# Execute action
switch ($Action.ToLower()) {
    "deploy" {
        Write-Status "Starting deployment..."
        Write-Host ""
        
        # Upload environment variables if script exists
        if (Test-Path "upload_env_to_aws.py") {
            Write-Status "Uploading environment variables to AWS Parameter Store..."
            python upload_env_to_aws.py
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Failed to upload env vars (may already exist)"
            }
            Write-Host ""
        }
        
        # Deploy agent
        Write-Status "Deploying agent: $AGENT_NAME"
        Write-Status "This will build Docker image, push to ECR, and deploy to Bedrock AgentCore..."
        Write-Host ""
        
        agentcore launch --agent $AGENT_NAME
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Status "✓ Deployment successful!"
            Write-Host ""
            Write-Status "Agent Details:"
            Write-Host "  Agent ID: $AGENT_ID"
            Write-Host "  Region: $REGION"
            Write-Host "  Endpoint: https://bedrock-agentcore.$REGION.amazonaws.com/agents/$AGENT_ID/invoke"
            Write-Host ""
            Write-Status "Test your agent with:"
            Write-Host "  agentcore invoke --agent $AGENT_NAME '{\"inputText\": \"Hello\"}'"
        } else {
            Write-Error "Deployment failed!"
            exit 1
        }
    }
    
    "status" {
        Write-Status "Checking agent status..."
        agentcore status --agent $AGENT_NAME
    }
    
    "test" {
        Write-Status "Testing agent..."
        $jsonBody = @{
            inputText = $TestMessage
        } | ConvertTo-Json -Compress
        agentcore invoke --agent $AGENT_NAME $jsonBody
    }
    
    "logs" {
        Write-Status "Fetching agent logs..."
        aws logs tail "/aws/bedrock-agentcore/$AGENT_NAME" --follow --region $REGION
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Logs may not be available yet. Try after first invocation."
        }
    }
    
    "delete" {
        Write-Warning "This will delete the agent: $AGENT_NAME"
        $confirm = Read-Host "Are you sure? (yes/no)"
        if ($confirm -eq "yes") {
            agentcore delete --agent $AGENT_NAME
            Write-Status "Agent deleted"
        } else {
            Write-Status "Deletion cancelled"
        }
    }
    
    "help" {
        Write-Host "Usage: .\deploy.ps1 [command] [options]"
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  deploy  - Deploy the agent (default)"
        Write-Host "  status  - Check agent status"
        Write-Host "  test    - Test the agent with a message"
        Write-Host "  logs    - View agent logs"
        Write-Host "  delete  - Delete the agent"
        Write-Host "  help    - Show this help message"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  .\deploy.ps1              # Deploy agent"
        Write-Host "  .\deploy.ps1 status        # Check status"
        Write-Host "  .\deploy.ps1 test         # Test with default message"
        Write-Host "  .\deploy.ps1 test 'Hello'  # Test with custom message"
        Write-Host "  .\deploy.ps1 logs          # View logs"
    }
    
    default {
        Write-Error "Unknown command: $Action"
        Write-Host "Use '.\deploy.ps1 help' for usage information"
        exit 1
    }
}

