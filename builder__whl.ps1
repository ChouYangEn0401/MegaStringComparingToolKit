# 檢查是否在虛擬環境
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Warning: You are not in a virtual environment. Please activate your venv first." -ForegroundColor Red
    exit
}

# 互動確認
$confirm = Read-Host "Are you sure you want to run this inside the venv? (y/n)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "Execution cancelled." -ForegroundColor Yellow
    exit
}

Write-Host "Upgrading build, setuptools, wheel..." -ForegroundColor Green
$pythonExe = if ($env:VIRTUAL_ENV) { Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe' } else { 'python' }
Write-Host "Using python: $pythonExe" -ForegroundColor Cyan
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install --upgrade build setuptools wheel

Write-Host "Building package..." -ForegroundColor Green
& $pythonExe -m build

Write-Host "Done!" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
