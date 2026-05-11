# IRT Security Check Script
Write-Host "Starting Full Security Check..." -ForegroundColor Cyan

# 1. Dependency Check
Write-Host "[1/3] Running pip-audit..." -ForegroundColor Yellow
pip-audit -r anket_sistemi/requirements.txt

# 2. Secret Scan (Manual Grep)
Write-Host "[2/3] Checking for hardcoded secrets..." -ForegroundColor Yellow
$secrets = Select-String -Path "anket_sistemi/backend/*.py" -Pattern "sk-", "AI_API_KEY", "PASSWORD", "SECRET_KEY"
if ($secrets) {
    Write-Host "Potential secrets found:" -ForegroundColor Red
    $secrets
} else {
    Write-Host "No hardcoded secrets found in backend code." -ForegroundColor Green
}

# 3. .gitignore Check
Write-Host "[3/3] Verifying .gitignore..." -ForegroundColor Yellow
$gi = Get-Content .gitignore
if ($gi -contains "SIFRELERIM_GİZLİ.txt" -and $gi -contains ".env") {
    Write-Host ".gitignore is correctly configured." -ForegroundColor Green
} else {
    Write-Host "WARNING: .gitignore might be missing critical files!" -ForegroundColor Red
}

Write-Host "Check Complete. See reports/security/final-security-report.md for details." -ForegroundColor Cyan
