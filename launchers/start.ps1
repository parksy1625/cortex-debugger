# Cortex Debugger M8 on Windows (PowerShell).
# Install Python 3.11+ first. The app is localhost-only.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$root = $PSScriptRoot
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.11 -m venv (Join-Path $root '.venv')
    } else {
        & python -m venv (Join-Path $root '.venv')
    }
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ required' }
}
$wheel = Get-ChildItem (Join-Path $root 'wheel') -Filter 'cortex_debugger-*.whl' | Select-Object -First 1
if (-not $wheel) { throw 'Cortex package wheel missing' }
$marker = Join-Path $root '.venv\.cortex-m11-ready'
if (-not (Test-Path $marker)) {
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }
    & $venvPython -m pip install 'torch==2.7.1'
    if ($LASTEXITCODE -ne 0) { throw 'PyTorch install failed' }
    & $venvPython -m pip install "$($wheel.FullName)[ml,api]"
    if ($LASTEXITCODE -ne 0) { throw 'Cortex dependency install failed' }
    New-Item -ItemType File -Path $marker -Force | Out-Null
}
# The GUI may set CORTEX_PAIRING_CODE itself and display it privately.
# Standalone PowerShell launch prints a new one-time code interactively.
if (-not $env:CORTEX_PAIRING_CODE) {
    $code = [System.Security.Cryptography.RandomNumberGenerator]::GetInt32(0, 1000000000)
    $env:CORTEX_PAIRING_CODE = $code.ToString('D9')
    Write-Host "Cortex pairing code: $env:CORTEX_PAIRING_CODE"
}
Write-Host 'Local app: http://127.0.0.1:8000/'
Write-Host 'Stop with Ctrl+C'
& $venvPython -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1
