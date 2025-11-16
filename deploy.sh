#!/bin/bash
# Deployment script for Bedrock AgentCore Agent
# Usage: ./deploy.sh [options]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AGENT_NAME="RitvikAgent"
REGION="us-west-2"
AGENT_ID="RitvikAgent-Nfl5014O49"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Bedrock AgentCore Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check if agentcore CLI is installed
if ! command -v agentcore &> /dev/null; then
    print_error "bedrock-agentcore-starter-toolkit is not installed"
    echo "Install it with: pip install bedrock-agentcore-starter-toolkit"
    exit 1
fi
print_status "✓ agentcore CLI found"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi
print_status "✓ AWS CLI found"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi
print_status "✓ AWS credentials configured"

# Check if .bedrock_agentcore.yaml exists
if [ ! -f ".bedrock_agentcore.yaml" ]; then
    print_error ".bedrock_agentcore.yaml not found"
    exit 1
fi
print_status "✓ Configuration file found"

echo ""

# Parse command line arguments
ACTION=${1:-deploy}

case $ACTION in
    deploy)
        print_status "Starting deployment..."
        echo ""
        
        # Step 1: Upload environment variables (if script exists)
        if [ -f "upload_env_to_aws.py" ]; then
            print_status "Uploading environment variables to AWS Parameter Store..."
            python upload_env_to_aws.py || print_warning "Failed to upload env vars (may already exist)"
            echo ""
        fi
        
        # Step 2: Deploy agent
        print_status "Deploying agent: $AGENT_NAME"
        print_status "This will build Docker image, push to ECR, and deploy to Bedrock AgentCore..."
        echo ""
        
        if agentcore launch --agent "$AGENT_NAME"; then
            echo ""
            print_status "✓ Deployment successful!"
            echo ""
            print_status "Agent Details:"
            echo "  Agent ID: $AGENT_ID"
            echo "  Region: $REGION"
            echo "  Endpoint: https://bedrock-agentcore.$REGION.amazonaws.com/agents/$AGENT_ID/invoke"
            echo ""
            print_status "Test your agent with:"
            echo "  agentcore invoke --agent $AGENT_NAME '{\"inputText\": \"Hello\"}'"
        else
            print_error "Deployment failed!"
            exit 1
        fi
        ;;
    
    status)
        print_status "Checking agent status..."
        agentcore status --agent "$AGENT_NAME"
        ;;
    
    test)
        print_status "Testing agent..."
        TEST_MESSAGE=${2:-"Hello, how are you?"}
        agentcore invoke --agent "$AGENT_NAME" "{\"inputText\": \"$TEST_MESSAGE\"}"
        ;;
    
    logs)
        print_status "Fetching agent logs..."
        aws logs tail "/aws/bedrock-agentcore/$AGENT_NAME" --follow --region "$REGION" || \
        print_warning "Logs may not be available yet. Try after first invocation."
        ;;
    
    delete)
        print_warning "This will delete the agent: $AGENT_NAME"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            agentcore delete --agent "$AGENT_NAME"
            print_status "Agent deleted"
        else
            print_status "Deletion cancelled"
        fi
        ;;
    
    help|--help|-h)
        echo "Usage: ./deploy.sh [command]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy the agent (default)"
        echo "  status  - Check agent status"
        echo "  test    - Test the agent with a message"
        echo "  logs    - View agent logs"
        echo "  delete  - Delete the agent"
        echo "  help    - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./deploy.sh              # Deploy agent"
        echo "  ./deploy.sh status       # Check status"
        echo "  ./deploy.sh test         # Test with default message"
        echo "  ./deploy.sh test 'Hello' # Test with custom message"
        echo "  ./deploy.sh logs         # View logs"
        ;;
    
    *)
        print_error "Unknown command: $ACTION"
        echo "Use './deploy.sh help' for usage information"
        exit 1
        ;;
esac

