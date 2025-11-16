# Fix Lambda IAM Permissions for Bedrock AgentCore
# This script adds the necessary permissions to your Lambda role

$ROLE_NAME = "TestlambdaforAgent-role-xmq700mb"  # Your existing role name
$REGION = "us-west-2"
$ACCOUNT_ID = "624571284647"
$AGENT_ID = "RitvikAgent-Nfl5014O49"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Fixing Lambda IAM Permissions" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Check if role exists
Write-Host "Checking IAM role..." -ForegroundColor Cyan
try {
    $role = aws iam get-role --role-name $ROLE_NAME 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Role '$ROLE_NAME' not found" -ForegroundColor Red
        Write-Host "Please check the role name in your Lambda function configuration" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✓ Role found: $ROLE_NAME" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Could not check role" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Create Bedrock AgentCore policy
$POLICY_NAME = "BedrockAgentCoreInvokePolicy"
Write-Host "Creating/updating Bedrock policy..." -ForegroundColor Cyan

$policyDocument = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "bedrock-agentcore:InvokeAgentRuntime"
            )
            Resource = @(
                "arn:aws:bedrock-agentcore:us-west-2:$ACCOUNT_ID:runtime/$AGENT_ID",
                "arn:aws:bedrock-agentcore:us-west-2:$ACCOUNT_ID:runtime/$AGENT_ID/*"
            )
        }
    )
} | ConvertTo-Json -Depth 10

$policyDocument | Out-File -FilePath "$env:TEMP\bedrock-policy.json" -Encoding utf8

# Check if policy exists
try {
    $existingPolicy = aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text 2>&1
    if ($existingPolicy -and $existingPolicy -ne "None") {
        Write-Host "Policy exists, updating..." -ForegroundColor Yellow
        # Delete old policy version and create new one
        $policyArn = $existingPolicy
        aws iam delete-policy --policy-arn $policyArn 2>&1 | Out-Null
    }
} catch {
    # Policy doesn't exist, will create new
}

# Create policy
try {
    $POLICY_ARN = aws iam create-policy `
        --policy-name $POLICY_NAME `
        --policy-document "file://$env:TEMP\bedrock-policy.json" `
        --query 'Policy.Arn' `
        --output text
    
    Write-Host "✓ Policy created: $POLICY_ARN" -ForegroundColor Green
} catch {
    # Try to get existing policy
    $POLICY_ARN = aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text
    if ($POLICY_ARN) {
        Write-Host "✓ Using existing policy: $POLICY_ARN" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Could not create or find policy" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Attach policy to role
Write-Host "Attaching policy to role..." -ForegroundColor Cyan
try {
    aws iam attach-role-policy `
        --role-name $ROLE_NAME `
        --policy-arn $POLICY_ARN
    
    Write-Host "✓ Policy attached to role!" -ForegroundColor Green
} catch {
    # Check if already attached
    $attachedPolicies = aws iam list-attached-role-policies --role-name $ROLE_NAME --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" --output text
    if ($attachedPolicies) {
        Write-Host "✓ Policy already attached to role" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Could not attach policy" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Also ensure basic Lambda execution role is attached
Write-Host "Checking Lambda execution permissions..." -ForegroundColor Cyan
$basicExecutionPolicy = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
try {
    aws iam attach-role-policy `
        --role-name $ROLE_NAME `
        --policy-arn $basicExecutionPolicy 2>&1 | Out-Null
    Write-Host "✓ Lambda execution permissions OK" -ForegroundColor Green
} catch {
    Write-Host "Note: Basic execution policy may already be attached" -ForegroundColor Yellow
}

Write-Host ""

# Cleanup
Remove-Item "$env:TEMP\bedrock-policy.json" -ErrorAction SilentlyContinue

Write-Host "==========================================" -ForegroundColor Green
Write-Host "✓ Permissions Fixed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The Lambda role now has permission to invoke Bedrock AgentCore." -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: It may take a few seconds for permissions to propagate." -ForegroundColor Yellow
Write-Host "If you still get errors, wait 10-30 seconds and try again." -ForegroundColor Yellow
Write-Host ""

