# Fix Lambda IAM Permissions for Bedrock AgentCore (Updated with wildcard)
# This script adds the necessary permissions including runtime-endpoint access

$ROLE_NAME = "TestlambdaforAgent-role-xmq700mb"
$REGION = "us-west-2"
$ACCOUNT_ID = "624571284647"
$AGENT_ID = "RitvikAgent-Nfl5014O49"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Fixing Lambda IAM Permissions (Updated)" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Check if role exists
Write-Host "Checking IAM role..." -ForegroundColor Cyan
try {
    $role = aws iam get-role --role-name $ROLE_NAME 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Role '$ROLE_NAME' not found" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Role found: $ROLE_NAME" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Could not check role" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Create/Update Bedrock AgentCore policy with wildcard for runtime-endpoint
$POLICY_NAME = "BedrockAgentCoreInvokePolicy"
Write-Host "Creating/updating Bedrock policy with wildcard support..." -ForegroundColor Cyan

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

# Check if policy exists and get its ARN
try {
    $existingPolicyArn = aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text 2>&1
    if ($existingPolicyArn -and $existingPolicyArn -ne "None") {
        Write-Host "Policy exists, creating new version..." -ForegroundColor Yellow
        
        # Get default version
        $defaultVersion = aws iam get-policy --policy-arn $existingPolicyArn --query 'Policy.DefaultVersionId' --output text
        
        # Create new policy version
        aws iam create-policy-version `
            --policy-arn $existingPolicyArn `
            --policy-document "file://$env:TEMP\bedrock-policy.json" `
            --set-as-default | Out-Null
        
        Write-Host "✓ Policy updated: $existingPolicyArn" -ForegroundColor Green
        $POLICY_ARN = $existingPolicyArn
    } else {
        throw
    }
} catch {
    # Create new policy
    Write-Host "Creating new policy..." -ForegroundColor Yellow
    $POLICY_ARN = aws iam create-policy `
        --policy-name $POLICY_NAME `
        --policy-document "file://$env:TEMP\bedrock-policy.json" `
        --query 'Policy.Arn' `
        --output text
    
    Write-Host "✓ Policy created: $POLICY_ARN" -ForegroundColor Green
}

Write-Host ""

# Detach old policy if attached, then attach new one
Write-Host "Updating role permissions..." -ForegroundColor Cyan

# Check if policy is attached
$attachedPolicies = aws iam list-attached-role-policies --role-name $ROLE_NAME --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" --output text

if ($attachedPolicies) {
    Write-Host "Policy already attached, detaching and reattaching..." -ForegroundColor Yellow
    aws iam detach-role-policy `
        --role-name $ROLE_NAME `
        --policy-arn $POLICY_ARN 2>&1 | Out-Null
    Start-Sleep -Seconds 2
}

# Attach policy to role
try {
    aws iam attach-role-policy `
        --role-name $ROLE_NAME `
        --policy-arn $POLICY_ARN
    
    Write-Host "✓ Policy attached to role!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Could not attach policy" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
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
Write-Host "Policy now includes:" -ForegroundColor Cyan
Write-Host "  - arn:aws:bedrock-agentcore:us-west-2:$ACCOUNT_ID:runtime/$AGENT_ID" -ForegroundColor White
Write-Host "  - arn:aws:bedrock-agentcore:us-west-2:$ACCOUNT_ID:runtime/$AGENT_ID/*" -ForegroundColor White
Write-Host ""
Write-Host "This covers both runtime and runtime-endpoint resources." -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Wait 30-60 seconds for IAM permissions to fully propagate." -ForegroundColor Yellow
Write-Host "Then test your Lambda function again." -ForegroundColor Yellow
Write-Host ""

