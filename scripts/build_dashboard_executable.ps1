param(
    [string]$PythonExecutable = "python",
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$DashboardConfig = "config/dashboard_github.toml"
)

$ErrorActionPreference = "Stop"

Push-Location $ProjectRoot
try {
    & $PythonExecutable -m pip install --upgrade pip
    & $PythonExecutable -m pip install ".[dashboard-build]"

    $version = (& $PythonExecutable -c "from src.reporting.dashboard_version import DASHBOARD_VERSION; print(DASHBOARD_VERSION)").Trim()
    if (-not $version) {
        throw "Impossible de determiner la version du dashboard."
    }

    & $PythonExecutable -m PyInstaller --noconfirm --clean packaging/dashboard_launcher.spec

    $bundleDir = Join-Path $ProjectRoot "dist\SalesDashboard"
    if (-not (Test-Path $bundleDir)) {
        throw "Le dossier dist\SalesDashboard n'a pas ete genere."
    }

    Copy-Item $DashboardConfig (Join-Path $bundleDir "dashboard_config.toml") -Force
    Copy-Item "scripts\update_dashboard_runtime.ps1" (Join-Path $bundleDir "update_dashboard_runtime.ps1") -Force

    $versionMetadata = [ordered]@{
        application = "SalesDashboard"
        version = $version
        channel = "stable"
        built_at = [DateTime]::UtcNow.ToString("o")
        config_file = "dashboard_config.toml"
    } | ConvertTo-Json -Depth 4
    Set-Content -Path (Join-Path $bundleDir "dashboard_version.json") -Value $versionMetadata -Encoding UTF8

    $zipPath = Join-Path $ProjectRoot "dist\SalesDashboard-win64-$version.zip"
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $bundleDir "*") -DestinationPath $zipPath

    Write-Host "BUNDLE_DIR=$bundleDir"
    Write-Host "ZIP_PATH=$zipPath"
}
finally {
    Pop-Location
}
