param(
    [string]$RuntimeRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$TaskName = "SalesPipelineMonthlyReport",
    [string]$Schedule = "Monthly",
    [int]$DayOfMonth = 2,
    [string]$StartTime = "06:00"
)

$ErrorActionPreference = "Stop"

$runScript = Join-Path $RuntimeRoot "scripts\run_pipeline.ps1"
if (-not (Test-Path $runScript)) {
    throw "Run script not found: $runScript"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runScript`" -RuntimeRoot `"$RuntimeRoot`""

$trigger = New-ScheduledTaskTrigger `
    -Monthly `
    -DaysOfMonth $DayOfMonth `
    -At $StartTime

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Monthly execution of the packaged sales pipeline."
