# Updated Permissions Fix - Runtime Endpoint Access

## Problem

The error shows the resource ARN includes `/runtime-endpoint/DEFAULT`:
```
arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49/runtime-endpoint/DEFAULT
```

The previous policy only allowed access to the base runtime resource, not the runtime-endpoint sub-resource.

## Solution

Updated the policy to include a **wildcard** that covers both:
- `arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49`
- `arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49/*`

## Quick Fix

### Run the Updated Script:

**Windows:**
```powershell
.\fix_permissions_updated.ps1
```

**Linux/Mac:**
```bash
chmod +x fix_permissions_updated.sh
./fix_permissions_updated.sh
```

## What Changed

The policy now includes **two resources**:
1. The base runtime resource
2. A wildcard `/*` to cover all sub-resources including `runtime-endpoint/DEFAULT`

## Updated Policy JSON

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49",
        "arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49/*"
      ]
    }
  ]
}
```

## Manual Fix in AWS Console

1. Go to **IAM** → **Policies**
2. Find `BedrockAgentCoreInvokePolicy`
3. Click **Edit policy**
4. Go to **JSON** tab
5. Update the Resource to include both:
   ```json
   "Resource": [
     "arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49",
     "arn:aws:bedrock-agentcore:us-west-2:624571284647:runtime/RitvikAgent-Nfl5014O49/*"
   ]
   ```
6. Click **Save changes**

## Important Notes

⚠️ **Wait 30-60 seconds** after updating the policy for IAM permissions to fully propagate.

IAM permissions can take up to 1 minute to propagate across all AWS services.

## Verify Permissions

After running the script, verify:

```bash
# List attached policies
aws iam list-attached-role-policies \
    --role-name TestlambdaforAgent-role-xmq700mb

# Get policy document
aws iam get-policy-version \
    --policy-arn <POLICY_ARN> \
    --version-id <VERSION_ID>
```

## Test Again

After waiting 30-60 seconds:

```bash
curl -X POST https://your-function-url.lambda-url.us-west-2.on.aws/invoke \
  -H "Content-Type: application/json" \
  -d '{"inputText": "Hello"}'
```

## If Still Getting Errors

1. **Wait longer**: IAM can take up to 2 minutes to propagate
2. **Check CloudWatch logs**: Look for more detailed error messages
3. **Verify policy version**: Make sure the default version includes the wildcard
4. **Try detaching and reattaching**: Sometimes helps with propagation

## Summary

✅ **Run the updated fix script**  
✅ **Wait 30-60 seconds** for propagation  
✅ **Test your Lambda function** again  

The wildcard `/*` should now cover the runtime-endpoint resource! 🎉

