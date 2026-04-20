param(
    [string]$InstallDir = (Split-Path -Parent $MyInvocation.MyCommand.Path),
    [string]$ManifestUrl = "https://raw.githubusercontent.com/JosueAfouda/automate-excel-with-python/executable/streamlit/published_app/dashboard_release.json"
)

$ErrorActionPreference = "Stop"

function Get-VersionParts([string]$Version) {
    if (-not $Version) {
        return @(0)
    }
    return ($Version -split '[^0-9]+' | Where-Object { $_ -ne "" } | ForEach-Object { [int]$_ })
}

function Compare-Version([string]$Left, [string]$Right) {
    $leftParts = Get-VersionParts $Left
    $rightParts = Get-VersionParts $Right
    $maxLength = [Math]::Max($leftParts.Count, $rightParts.Count)

    for ($index = 0; $index -lt $maxLength; $index++) {
        $leftValue = if ($index -lt $leftParts.Count) { $leftParts[$index] } else { 0 }
        $rightValue = if ($index -lt $rightParts.Count) { $rightParts[$index] } else { 0 }

        if ($leftValue -lt $rightValue) { return -1 }
        if ($leftValue -gt $rightValue) { return 1 }
    }

    return 0
}

$versionFile = Join-Path $InstallDir "dashboard_version.json"
$currentVersion = "0.0.0"
if (Test-Path $versionFile) {
    $currentVersion = (Get-Content $versionFile -Raw | ConvertFrom-Json).version
}

$manifest = Invoke-RestMethod -Uri $ManifestUrl -Method Get
if (-not $manifest.windows_package_url) {
    throw "Le manifeste ne contient pas de package Windows publie."
}

if ((Compare-Version $currentVersion $manifest.version) -ge 0) {
    Write-Host "Le dashboard est deja a jour ($currentVersion)."
    exit 0
}

Write-Host "Mise a jour detectee: $currentVersion -> $($manifest.version)"
Write-Host "Fermez l'application avant de poursuivre."

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("sales-dashboard-update-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempRoot | Out-Null
$zipPath = Join-Path $tempRoot "dashboard-update.zip"
$extractDir = Join-Path $tempRoot "extracted"

Invoke-WebRequest -Uri $manifest.windows_package_url -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force
Copy-Item (Join-Path $extractDir "*") $InstallDir -Recurse -Force

Write-Host "Mise a jour installee dans $InstallDir"
