# PowerShell script to deploy Bedrock AgentCore API to AWS Lambda

$FUNCTION_NAME = "bedrock-agentcore-api"
$REGION = "us-west-2"
$RUNTIME = "python3.11"
$HANDLER = "lambda_function.lambda_handler"
$ROLE_NAME = "bedrock-agentcore-lambda-role"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Deploying to AWS Lambda" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Check AWS CLI
try {
    $null = Get-Command aws -ErrorAction Stop
} catch {
    Write-Host "ERROR: AWS CLI not found. Install from https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# Check if function exists
try {
    $null = aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>&1
    $UPDATE_MODE = $true
    Write-Host "Function exists, updating..." -ForegroundColor Yellow
} catch {
    $UPDATE_MODE = $false
    Write-Host "Function does not exist, creating..." -ForegroundColor Yellow
}

# Create deployment package
Write-Host "Creating deployment package..." -ForegroundColor Cyan
Compress-Archive -Path * -DestinationPath deployment.zip -Force
Write-Host "Package created: deployment.zip" -ForegroundColor Green
Write-Host ""

# Get or create IAM role
Write-Host "Setting up IAM role..." -ForegroundColor Cyan
try {
    $ROLE_ARN = aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Host "Creating IAM role..." -ForegroundColor Yellow
    
    # Create trust policy
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
    
    $trustPolicy | Out-File -FilePath trust-policy.json -Encoding utf8
    
    # Create role
    aws iam create-role `
        --role-name $ROLE_NAME `
        --assume-role-policy-document file://trust-policy.json `
        --description "Role for Bedrock AgentCore Lambda function"
    
    # Attach policies
    aws iam attach-role-policy `
        --role-name $ROLE_NAME `
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Wait for role
    Start-Sleep -Seconds 5
    
    $ROLE_ARN = aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text
    
    Remove-Item trust-policy.json
}

Write-Host "Using IAM role: $ROLE_ARN" -ForegroundColor Green
Write-Host ""

# Deploy function
if ($UPDATE_MODE) {
    Write-Host "Updating Lambda function..." -ForegroundColor Cyan
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file fileb://deployment.zip `
        --region $REGION
    
    Write-Host "Waiting for update to complete..." -ForegroundColor Yellow
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
        --zip-file fileb://deployment.zip `
        --timeout 300 `
        --memory-size 512 `
        --region $REGION `
        --environment "Variables={AWS_REGION=$REGION}"
    
    Write-Host "✓ Function created!" -ForegroundColor Green
}

Write-Host ""

# Get or create function URL
Write-Host "Setting up API endpoint..." -ForegroundColor Cyan
try {
    $FUNCTION_URL = aws lambda get-function-url-config `
        --function-name $FUNCTION_NAME `
        --region $REGION `
        --query 'FunctionUrl' `
        --output text 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Host "Creating function URL..." -ForegroundColor Yellow
    aws lambda create-function-url-config `
        --function-name $FUNCTION_NAME `
        --auth-type NONE `
        --cors '{"AllowOrigins": ["*"], "AllowMethods": ["*"], "AllowHeaders": ["*"]}' `
        --region $REGION
    
    $FUNCTION_URL = aws lambda get-function-url-config `
        --function-name $FUNCTION_NAME `
        --region $REGION `
        --query 'FunctionUrl' `
        --output text
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Function URL: $FUNCTION_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test endpoints:" -ForegroundColor Yellow
Write-Host "  GET  $FUNCTION_URL/health"
Write-Host "  GET  $FUNCTION_URL/status"
Write-Host "  POST $FUNCTION_URL/invoke"
Write-Host "  POST $FUNCTION_URL/webhook"
Write-Host ""

# Cleanup
Remove-Item -Path deployment.zip -ErrorAction SilentlyContinue

