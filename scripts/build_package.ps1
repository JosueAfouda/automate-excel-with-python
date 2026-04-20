param(
    [string]$PythonExecutable = "python",
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"

Push-Location $ProjectRoot
try {
    & $PythonExecutable -m pip install --upgrade build
    & $PythonExecutable -m build
}
finally {
    Pop-Location
}
