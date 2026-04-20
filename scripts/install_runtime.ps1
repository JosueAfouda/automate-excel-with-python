param(
    [string]$PythonExecutable = "python",
    [string]$InstallRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"

$venvPath = Join-Path $InstallRoot ".venv"

if (-not (Test-Path $venvPath)) {
    & $PythonExecutable -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"

Push-Location $InstallRoot
try {
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install .
}
finally {
    Pop-Location
}

Write-Host "Runtime installed successfully."
Write-Host "Virtual environment: $venvPath"
Write-Host "Next step: run scripts\check_environment.ps1"
