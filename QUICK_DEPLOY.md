# Quick Deploy Guide

## One-Command Deploy

```bash
# Windows PowerShell
.\deploy.ps1

# Linux/Mac
./deploy.sh
```

Or directly:
```bash
agentcore launch --agent RitvikAgent
```

---

## What Gets Deployed

✅ Your FastAPI agent (`agent.py`)  
✅ All dependencies from `requirements.txt`  
✅ Environment variables from AWS Parameter Store  
✅ Docker container to ECR  
✅ Agent runtime on Bedrock AgentCore  

---

## After Deployment

**Your endpoint will be:**
```
https://bedrock-agentcore.us-west-2.amazonaws.com/agents/RitvikAgent-Nfl5014O49/invoke
```

**Test it:**
```bash
# Using the script
./deploy.sh test

# Or directly
agentcore invoke --agent RitvikAgent '{"inputText": "Hello"}'
```

---

## Common Commands

```bash
# Deploy
agentcore launch --agent RitvikAgent

# Check status
agentcore status --agent RitvikAgent

# Test
agentcore invoke --agent RitvikAgent '{"inputText": "Hello"}'

# View logs
aws logs tail /aws/bedrock-agentcore/RitvikAgent --follow --region us-west-2

# Update (re-deploy)
agentcore launch --agent RitvikAgent
```

---

## Troubleshooting

**Build fails?**
- Check Dockerfile: `.bedrock_agentcore/RitvikAgent/Dockerfile`
- Verify requirements.txt is correct

**Push fails?**
- Login to ECR: `aws ecr get-login-password --region us-west-2 | docker login ...`

**Deploy fails?**
- Check IAM permissions
- Verify AWS credentials: `aws sts get-caller-identity`

---

## Full Documentation

See `DEPLOYMENT_GUIDE.md` for complete details.

