# PowerShell script to deploy Bedrock AgentCore Lambda Function

$FUNCTION_NAME = "bedrock-agent-lambda"
$REGION = "us-west-2"
$RUNTIME = "python3.11"
$HANDLER = "bedrock_agent_lambda.lambda_handler"
$ROLE_NAME = "bedrock-agent-lambda-role"
$ZIP_FILE = "bedrock_lambda_deployment.zip"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Deploying Bedrock Agent Lambda Function" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Check AWS CLI
try {
    $null = Get-Command aws -ErrorAction Stop
} catch {
    Write-Host "ERROR: AWS CLI not found" -ForegroundColor Red
    exit 1
}

# Check if function exists
try {
    $null = aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>&1 | Out-Null
    $UPDATE_MODE = $true
    Write-Host "✓ Function exists, will update..." -ForegroundColor Yellow
} catch {
    $UPDATE_MODE = $false
    Write-Host "✓ Function does not exist, will create..." -ForegroundColor Yellow
}

# Create deployment package
Write-Host ""
Write-Host "Creating deployment package..." -ForegroundColor Cyan
Remove-Item -Path $ZIP_FILE -ErrorAction SilentlyContinue

# Create zip with just the Lambda function (self-contained, no utils dependency)
Compress-Archive -Path bedrock_agent_lambda.py -DestinationPath $ZIP_FILE -Force
Write-Host "✓ Package created: $ZIP_FILE" -ForegroundColor Green
Write-Host ""

# Get or create IAM role
Write-Host "Setting up IAM role..." -ForegroundColor Cyan
try {
    $ROLE_ARN = aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "✓ Using existing role: $ROLE_ARN" -ForegroundColor Green
} catch {
    Write-Host "Creating IAM role..." -ForegroundColor Yellow
    
    $trustPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Principal = @{
                    Service = "lambda.amazonaws.com"
                }
                Action = "sts:AssumeRole"
            }
        )
    } | ConvertTo-Json -Depth 10
    
    $trustPolicy | Out-File -FilePath "$env:TEMP\trust-policy.json" -Encoding utf8
    
    aws iam create-role `
        --role-name $ROLE_NAME `
        --assume-role-policy-document "file://$env:TEMP\trust-policy.json" `
        --description "Role for Bedrock Agent Lambda function" | Out-Null
    
    aws iam attach-role-policy `
        --role-name $ROLE_NAME `
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole | Out-Null
    
    Start-Sleep -Seconds 5
    $ROLE_ARN = aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text
    
    Remove-Item "$env:TEMP\trust-policy.json" -ErrorAction SilentlyContinue
    Write-Host "✓ Role created: $ROLE_ARN" -ForegroundColor Green
}

# Add Bedrock permissions
Write-Host ""
Write-Host "Configuring Bedrock permissions..." -ForegroundColor Cyan

$POLICY_NAME = "BedrockAgentCoreInvokePolicy"
$ACCOUNT_ID = "624571284647"
$AGENT_ID = "RitvikAgent-Nfl5014O49"

try {
    $POLICY_ARN = aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text 2>&1
    if ([string]::IsNullOrEmpty($POLICY_ARN)) { throw }
    Write-Host "✓ Policy exists: $POLICY_ARN" -ForegroundColor Green
} catch {
    Write-Host "Creating Bedrock policy..." -ForegroundColor Yellow
    $bedrockPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Action = @("bedrock-agentcore:InvokeAgentRuntime")
                Resource = "arn:aws:bedrock-agentcore:us-west-2:${ACCOUNT_ID}:runtime/${AGENT_ID}"
            }
        )
    } | ConvertTo-Json -Depth 10
    
    $bedrockPolicy | Out-File -FilePath "$env:TEMP\bedrock-policy.json" -Encoding utf8
    
    $POLICY_ARN = aws iam create-policy `
        --policy-name $POLICY_NAME `
        --policy-document "file://$env:TEMP\bedrock-policy.json" `
        --query 'Policy.Arn' `
        --output text
    
    Remove-Item "$env:TEMP\bedrock-policy.json" -ErrorAction SilentlyContinue
    Write-Host "✓ Policy created: $POLICY_ARN" -ForegroundColor Green
}

# Attach policy to role
Write-Host "Attaching policy to role..." -ForegroundColor Cyan
try {
    aws iam attach-role-policy `
        --role-name $ROLE_NAME `
        --policy-arn $POLICY_ARN 2>&1 | Out-Null
    Write-Host "✓ Policy attached to role" -ForegroundColor Green
} catch {
    # Check if already attached
    $attached = aws iam list-attached-role-policies --role-name $ROLE_NAME --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" --output text
    if ($attached) {
        Write-Host "✓ Policy already attached" -ForegroundColor Green
    } else {
        Write-Host "⚠ Warning: Could not attach policy (may already be attached)" -ForegroundColor Yellow
    }
}

Write-Host "✓ Permissions configured" -ForegroundColor Green
Write-Host ""

# Deploy function
if ($UPDATE_MODE) {
    Write-Host "Updating Lambda function..." -ForegroundColor Cyan
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file "fileb://$ZIP_FILE" `
        --region $REGION | Out-Null
    
    Write-Host "Waiting for update..." -ForegroundColor Yellow
    aws lambda wait function-updated `
        --function-name $FUNCTION_NAME `
        --region $REGION
    
    Write-Host "✓ Function updated!" -ForegroundColor Green
} else {
    Write-Host "Creating Lambda function..." -ForegroundColor Cyan
    aws lambda create-function `
        --function-name $FUNCTION_NAME `
        --runtime $RUNTIME `
        --role $ROLE_ARN `
        --handler $HANDLER `
        --zip-file "fileb://$ZIP_FILE" `
        --timeout 300 `
        --memory-size 512 `
        --region $REGION `
        --environment "Variables={AWS_REGION=$REGION,BEDROCK_AGENT_ID=RitvikAgent-Nfl5014O49,AWS_ACCOUNT_ID=624571284647}" | Out-Null
    
    Write-Host "✓ Function created!" -ForegroundColor Green
}

Write-Host ""

# Create or get Function URL
Write-Host "Setting up Function URL..." -ForegroundColor Cyan
try {
    $FUNCTION_URL = aws lambda get-function-url-config `
        --function-name $FUNCTION_NAME `
        --region $REGION `
        --query 'FunctionUrl' `
        --output text 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "✓ Function URL exists" -ForegroundColor Green
} catch {
    Write-Host "Creating Function URL..." -ForegroundColor Yellow
    aws lambda create-function-url-config `
        --function-name $FUNCTION_NAME `
        --auth-type NONE `
        --cors '{"AllowOrigins": ["*"], "AllowMethods": ["*"], "AllowHeaders": ["*"]}' `
        --region $REGION | Out-Null
    
    $FUNCTION_URL = aws lambda get-function-url-config `
        --function-name $FUNCTION_NAME `
        --region $REGION `
        --query 'FunctionUrl' `
        --output text
    
    Write-Host "✓ Function URL created!" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Function Name: $FUNCTION_NAME" -ForegroundColor Cyan
Write-Host "Function URL:  $FUNCTION_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test endpoints:" -ForegroundColor Yellow
Write-Host "  GET  $FUNCTION_URL/health"
Write-Host "  GET  $FUNCTION_URL/status"
Write-Host "  POST $FUNCTION_URL/invoke"
Write-Host "  POST $FUNCTION_URL/webhook"
Write-Host ""

# Cleanup
Remove-Item -Path $ZIP_FILE -ErrorAction SilentlyContinue

