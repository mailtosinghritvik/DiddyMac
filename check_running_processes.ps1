# PowerShell script to check for running Python processes related to DiddyMac
# This helps identify if multiple servers are running simultaneously

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "CHECKING FOR RUNNING DIDDYMAC PROCESSES" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

# Check for Python processes
Write-Host "`n1. All Python Processes:" -ForegroundColor Yellow
Get-Process python* -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, CPU, WorkingSet | Format-Table -AutoSize

# Check for processes using ports 8000 and 8080
Write-Host "`n2. Processes Using Port 8000 (webhook_server, bedrock_api_server):" -ForegroundColor Yellow
$port8000 = netstat -ano | Select-String ":8000" | Select-String "LISTENING"
if ($port8000) {
    Write-Host $port8000 -ForegroundColor Green
    $port8000 | ForEach-Object {
        $pid = ($_ -split '\s+')[-1]
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  PID $pid - $($process.ProcessName) - $($process.Path)" -ForegroundColor White
        }
    }
} else {
    Write-Host "  No process listening on port 8000" -ForegroundColor Gray
}

Write-Host "`n3. Processes Using Port 8080 (agent.py for AWS Bedrock):" -ForegroundColor Yellow
$port8080 = netstat -ano | Select-String ":8080" | Select-String "LISTENING"
if ($port8080) {
    Write-Host $port8080 -ForegroundColor Green
    $port8080 | ForEach-Object {
        $pid = ($_ -split '\s+')[-1]
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  PID $pid - $($process.ProcessName) - $($process.Path)" -ForegroundColor White
        }
    }
} else {
    Write-Host "  No process listening on port 8080" -ForegroundColor Gray
}

# Check for uvicorn processes (FastAPI server)
Write-Host "`n4. Uvicorn/FastAPI Processes:" -ForegroundColor Yellow
$uvicornProcesses = Get-Process | Where-Object { $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*agent.py*" } -ErrorAction SilentlyContinue
if ($uvicornProcesses) {
    $uvicornProcesses | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize
} else {
    Write-Host "  No uvicorn processes found" -ForegroundColor Gray
}

# Check for Flask processes (webhook_server)
Write-Host "`n5. Flask/Webhook Server Processes:" -ForegroundColor Yellow
$flaskProcesses = Get-Process | Where-Object { $_.CommandLine -like "*flask*" -or $_.CommandLine -like "*webhook_server*" } -ErrorAction SilentlyContinue
if ($flaskProcesses) {
    $flaskProcesses | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize
} else {
    Write-Host "  No Flask processes found" -ForegroundColor Gray
}

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

Write-Host "`nTo kill a specific process, use:" -ForegroundColor Yellow
Write-Host "  Stop-Process -Id <PID> -Force" -ForegroundColor White

Write-Host "`nTo kill all Python processes (CAUTION!):" -ForegroundColor Yellow
Write-Host "  Get-Process python* | Stop-Process -Force" -ForegroundColor White

Write-Host "`nTo start only ONE server:" -ForegroundColor Yellow
Write-Host "  For AWS Bedrock Agent Core: python agent.py" -ForegroundColor White
Write-Host "  For Webhook Server: python webhook_server.py" -ForegroundColor White
Write-Host "  For API Server: python bedrock_api_server.py" -ForegroundColor White

Write-Host "`n" -NoNewline

