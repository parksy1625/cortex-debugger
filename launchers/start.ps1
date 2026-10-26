param([switch]$Check)
# Cortex Debugger M12 on Windows (PowerShell).
# Install Python 3.11+ first. The app is localhost-only.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$root = $PSScriptRoot
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (Test-Path $venvPython) {
    $pythonCommand = $venvPython
    $pythonArguments = @()
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = 'py'
    # Resolve an installed Python 3 runtime, not only precisely Python 3.11.
    # The shared preflight enforces the minimum supported version (3.11).
    $pythonArguments = @('-3')
} else {
    $pythonCommand = 'python'
    $pythonArguments = @()
}
& $pythonCommand @pythonArguments (Join-Path $root 'runtime-preflight.py')
if ($LASTEXITCODE -ne 0) { throw 'Cortex M12 preflight failed' }
if ($Check) { return }
if (-not $env:CORTEX_PAIRING_CODE -and [Console]::IsOutputRedirected) {
    throw 'Cannot display a pairing code with redirected output. Run in an interactive terminal or provide CORTEX_PAIRING_CODE through your launcher.'
}
if (-not (Test-Path $venvPython)) {
    & $pythonCommand @pythonArguments -m venv (Join-Path $root '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ required' }
}
$wheel = Get-ChildItem (Join-Path $root 'wheel') -Filter 'cortex_debugger-*.whl' | Select-Object -First 1
if (-not $wheel) { throw 'Cortex package wheel missing' }
$marker = Join-Path $root '.venv\.cortex-runtime-wheel-sha256'
$wheelSha256 = (Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$installedSha256 = if (Test-Path $marker) { (Get-Content -LiteralPath $marker -Raw).Trim() } else { '' }
if ($installedSha256 -ne $wheelSha256) {
    Write-Host 'Preparing Cortex runtime dependencies for this bundle (first setup may take a while)...'
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }
    & $venvPython -m pip install 'torch==2.7.1'
    if ($LASTEXITCODE -ne 0) { throw 'PyTorch install failed' }
    & $venvPython -m pip install "$($wheel.FullName)[ml,api]"
    if ($LASTEXITCODE -ne 0) { throw 'Cortex dependency install failed' }
    # Record success only after every dependency was installed.
    $temporaryMarker = "$marker.$PID.tmp"
    Set-Content -LiteralPath $temporaryMarker -Value $wheelSha256 -NoNewline
    Move-Item -LiteralPath $temporaryMarker -Destination $marker -Force
}
# The GUI may set CORTEX_PAIRING_CODE itself and display it privately.
# Standalone PowerShell launch prints a new one-time code only to a terminal.
if (-not $env:CORTEX_PAIRING_CODE) {
    $code = [System.Security.Cryptography.RandomNumberGenerator]::GetInt32(0, 1000000000)
    $env:CORTEX_PAIRING_CODE = $code.ToString('D9')
    Write-Host "Cortex pairing code: $env:CORTEX_PAIRING_CODE"
}
# Local Windows owner control uses explicit current-SID DACL and
# request-time named-pipe impersonation. HTTP retains browser pairing.
$env:CORTEX_OWNER_IPC = '1'
Write-Host 'Local app: http://127.0.0.1:8000/'
Write-Host 'Stop with Ctrl+C'
& $venvPython -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1
