# Lambda Permissions Fix Guide

## Problem

Your Lambda function is getting this error:
```
User: arn:aws:sts::624571284647:assumed-role/TestlambdaforAgent-role-xmq700mb/TestlambdaforAgent 
is not authorized to perform: bedrock-agentcore:InvokeAgentRuntime
```

## Solution

The Lambda role needs permission to invoke Bedrock AgentCore. Run the fix script:

### Windows:
```powershell
.\fix_lambda_permissions.ps1
```

### Linux/Mac:
```bash
chmod +x fix_lambda_permissions.sh
./fix_lambda_permissions.sh
```

## What the Script Does

1. ✅ Checks if your Lambda role exists
2. ✅ Creates IAM policy for Bedrock AgentCore access
3. ✅ Attaches policy to your Lambda role
4. ✅ Ensures basic Lambda execution permissions

## Manual Fix (Alternative)

If you prefer to fix it manually:

### Step 1: Create IAM Policy

1. Go to **AWS Console** → **IAM** → **Policies**
2. Click **Create policy**
3. Go to **JSON** tab
4. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": "arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49"
    }
  ]
}
```

5. Name it: `BedrockAgentCoreInvokePolicy`
6. Click **Create policy**

### Step 2: Attach Policy to Role

1. Go to **IAM** → **Roles**
2. Find your role: `TestlambdaforAgent-role-xmq700mb`
3. Click on the role
4. Click **Add permissions** → **Attach policies**
5. Search for `BedrockAgentCoreInvokePolicy`
6. Select it and click **Add permissions**

## Verify Permissions

After running the script, verify:

```bash
# List attached policies
aws iam list-attached-role-policies \
    --role-name TestlambdaforAgent-role-xmq700mb
```

You should see `BedrockAgentCoreInvokePolicy` in the list.

## Test Again

After fixing permissions, wait 10-30 seconds for propagation, then test:

```bash
curl -X POST https://your-function-url.lambda-url.us-west-2.on.aws/invoke \
  -H "Content-Type: application/json" \
  -d '{"inputText": "Hello"}'
```

## If Still Getting Errors

1. **Wait longer**: IAM permissions can take up to 1 minute to propagate
2. **Check role name**: Make sure the role name in the script matches your Lambda role
3. **Check resource ARN**: Verify the agent ARN is correct
4. **Check CloudWatch logs**: Look for more detailed error messages

## Update Deployment Script

The deployment scripts (`deploy_bedrock_lambda.ps1` and `deploy_bedrock_lambda.sh`) have been updated to automatically add these permissions. If you redeploy, permissions will be set automatically.

## Summary

✅ **Run the fix script** to add Bedrock permissions  
✅ **Wait 10-30 seconds** for propagation  
✅ **Test your Lambda function** again  

The permission error should be resolved! 🎉

