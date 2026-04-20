param(
    [string]$RuntimeRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"

$venvExe = Join-Path $RuntimeRoot ".venv\Scripts\sales-pipeline.exe"

if (-not (Test-Path $venvExe)) {
    throw "sales-pipeline executable not found. Run scripts\install_runtime.ps1 first."
}

$defaultConfig = Join-Path $RuntimeRoot "config\prod.toml"
$arguments = @("check", "--runtime-root", $RuntimeRoot)

if ($ConfigPath -ne "") {
    $arguments += @("--config", $ConfigPath)
}
elseif (Test-Path $defaultConfig) {
    $arguments += @("--config", $defaultConfig)
}

& $venvExe @arguments
exit $LASTEXITCODE
