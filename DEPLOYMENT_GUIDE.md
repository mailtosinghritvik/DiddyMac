# AWS Bedrock AgentCore Deployment Guide

## Quick Deploy

Your agent is already configured! To deploy:

```bash
# Deploy the agent
agentcore launch --agent RitvikAgent
```

That's it! The CLI will:
1. Build the Docker image
2. Push to ECR
3. Deploy to Bedrock AgentCore

---

## Prerequisites

### 1. Install Bedrock AgentCore CLI

```bash
pip install bedrock-agentcore-starter-toolkit
```

### 2. Configure AWS Credentials

```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-west-2
```

### 3. Verify Configuration

Check your `.bedrock_agentcore.yaml` file - it's already configured with:
- **Agent Name**: `RitvikAgent`
- **Agent ID**: `RitvikAgent-Nfl5014O49`
- **Region**: `us-west-2`
- **ECR Repository**: `624571284647.dkr.ecr.us-west-2.amazonaws.com/bedrock-agentcore-ritvikagent`

---

## Deployment Steps

### Step 1: Verify Your Setup

```bash
# Check agent configuration
agentcore status --agent RitvikAgent

# Or view config
cat .bedrock_agentcore.yaml
```

### Step 2: Deploy the Agent

```bash
# Deploy (this builds, pushes, and deploys)
agentcore launch --agent RitvikAgent
```

**What happens:**
- Builds Docker image from `.bedrock_agentcore/RitvikAgent/Dockerfile`
- Pushes image to ECR
- Creates/updates the agent in Bedrock AgentCore
- Returns agent ARN and endpoint

### Step 3: Verify Deployment

```bash
# Check agent status
agentcore status --agent RitvikAgent

# Get agent details
aws bedrock-agentcore get-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2
```

### Step 4: Test the Deployment

```bash
# Test with a simple message
agentcore invoke --agent RitvikAgent '{"inputText": "Hello, how are you?"}'

# Or using AWS CLI
aws bedrock-agentcore invoke-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2 \
    --input '{"inputText": "Hello, how are you?"}'
```

---

## Deployment Options

### Deploy with Specific Configuration

```bash
# Deploy with custom settings
agentcore launch \
    --agent RitvikAgent \
    --region us-west-2 \
    --network-mode PUBLIC \
    --protocol HTTP
```

### Update Existing Deployment

```bash
# Re-deploy (updates existing agent)
agentcore launch --agent RitvikAgent
```

This will:
- Rebuild the Docker image
- Push new image to ECR
- Update the agent runtime

### Deploy New Version

```bash
# Deploy as new version
agentcore launch --agent RitvikAgent --version v2
```

---

## Environment Variables

Your agent loads environment variables from AWS Parameter Store. Make sure they're set:

```bash
# Upload environment variables to AWS Parameter Store
python upload_env_to_aws.py
```

Or set them in `.env` file (for local testing).

---

## Monitoring & Logs

### View Agent Logs

```bash
# View CloudWatch logs
aws logs tail /aws/bedrock-agentcore/RitvikAgent --follow --region us-west-2
```

### Enable Observability

```bash
# Enable CloudWatch Transaction Search
agentcore enable-observability --agent RitvikAgent
```

### Check Agent Status

```bash
# Get agent status
agentcore status --agent RitvikAgent

# Or via AWS CLI
aws bedrock-agentcore get-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2 \
    --query 'agent.status'
```

---

## Troubleshooting

### Build Fails

**Issue**: Docker build fails
```bash
# Check Dockerfile
cat .bedrock_agentcore/RitvikAgent/Dockerfile

# Test build locally
docker build -f .bedrock_agentcore/RitvikAgent/Dockerfile -t test-agent .
```

### Push to ECR Fails

**Issue**: Cannot push to ECR
```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 624571284647.dkr.ecr.us-west-2.amazonaws.com

# Verify ECR repository exists
aws ecr describe-repositories --region us-west-2
```

### Deployment Fails

**Issue**: Agent deployment fails
```bash
# Check IAM permissions
aws iam get-role --role-name AmazonBedrockAgentCoreSDKRuntime-us-west-2-b304167607

# Verify execution role has correct permissions
aws iam list-attached-role-policies \
    --role-name AmazonBedrockAgentCoreSDKRuntime-us-west-2-b304167607
```

### Agent Not Responding

**Issue**: Agent deployed but not responding
```bash
# Check agent health
agentcore status --agent RitvikAgent

# Test endpoint directly
curl -X POST https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke \
  -H "Content-Type: application/json" \
  -d '{"inputText": "test"}' \
  --aws-sigv4 "aws:amz:us-west-2:bedrock-agentcore"
```

---

## Configuration Details

### Current Configuration

From `.bedrock_agentcore.yaml`:

```yaml
RitvikAgent:
  name: RitvikAgent
  entrypoint: agent.py
  deployment_type: container
  platform: linux/arm64
  aws:
    account: '624571284647'
    region: us-west-2
    execution_role: arn:aws:iam::624571284647:role/AmazonBedrockAgentCoreSDKRuntime-us-west-2-b304167607
    ecr_repository: 624571284647.dkr.ecr.us-west-2.amazonaws.com/bedrock-agentcore-ritvikagent
  network_configuration:
    network_mode: PUBLIC
  protocol_configuration:
    server_protocol: HTTP
  observability:
    enabled: true
  memory:
    mode: STM_AND_LTM
    memory_name: RitvikAgent_mem
```

### Network Configuration

- **Network Mode**: `PUBLIC` - Accessible from internet
- **Protocol**: `HTTP` - Uses HTTP protocol on port 8080

### Memory Configuration

- **Mode**: `STM_AND_LTM` - Short-term and long-term memory enabled
- **Memory Name**: `RitvikAgent_mem`
- **Event Expiry**: 30 days

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Bedrock AgentCore

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Install Bedrock AgentCore CLI
        run: pip install bedrock-agentcore-starter-toolkit
      
      - name: Deploy Agent
        run: agentcore launch --agent RitvikAgent
```

---

## Rollback

### Rollback to Previous Version

```bash
# List agent versions
aws bedrock-agentcore list-agent-versions \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2

# Rollback (if versioning is enabled)
agentcore rollback --agent RitvikAgent --version previous
```

---

## Cleanup

### Delete Agent

```bash
# Delete the agent
agentcore delete --agent RitvikAgent

# Or via AWS CLI
aws bedrock-agentcore delete-agent \
    --agent-id RitvikAgent-Nfl5014O49 \
    --region us-west-2
```

**Warning**: This permanently deletes the agent and all associated resources.

---

## Next Steps

After deployment:

1. **Test the endpoint**: Use the API client or curl examples
2. **Monitor logs**: Set up CloudWatch alarms
3. **Set up alerts**: Configure SNS notifications
4. **Document API**: Share endpoint with your team
5. **Integrate**: Use the API client in your applications

---

## Quick Reference

```bash
# Deploy
agentcore launch --agent RitvikAgent

# Status
agentcore status --agent RitvikAgent

# Test
agentcore invoke --agent RitvikAgent '{"inputText": "Hello"}'

# Logs
aws logs tail /aws/bedrock-agentcore/RitvikAgent --follow

# Delete
agentcore delete --agent RitvikAgent
```

---

## Support

- **AWS Documentation**: https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html
- **AgentCore CLI**: `agentcore --help`
- **AWS Support**: AWS Support Center

