# Register/update the "create one WeChat draft" scheduled task.
#
#   Every scheduler.interval_days at scheduler.time (read from config.yaml,
#   default every 2 days at 08:00) -> python main.py daily (create_draft only,
#   never publish_draft / mass send -- see AGENTS.md).
#
# Usage (no admin needed for a task in the root folder of the current user):
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\win\register-task.ps1
#
# NOTE: kept ASCII-only on purpose. Windows PowerShell 5.1 reads .ps1 files
#       without a BOM as ANSI/GBK, so non-ASCII comments can break parsing.

$ErrorActionPreference = 'Stop'

$projectDir = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$vbs = Join-Path $projectDir 'scripts\win\run-hidden.vbs'
$cmd = Join-Path $projectDir 'scripts\win\run-daily.cmd'
$taskName = 'FeiyingqiWechatAINews-Draft'

if (-not (Test-Path $vbs)) { throw "not found: $vbs" }
if (-not (Test-Path $cmd)) { throw "not found: $cmd" }

$action = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument ('"{0}" "{1}"' -f $vbs, $cmd)

# Read scheduler.time / scheduler.interval_days from config.yaml so the task
# trigger and the app config cannot drift apart (single source of truth).
# Keep this parser ASCII-only: it only needs two scalar keys.
$schedTime = '08:00'
$schedDays = 2
$cfgPath = Join-Path $projectDir 'config.yaml'
if (Test-Path $cfgPath) {
    $cfgLines = Get-Content $cfgPath -Encoding UTF8
    $inSched = $false
    foreach ($line in $cfgLines) {
        if ($line -match '^scheduler:\s*$') { $inSched = $true; continue }
        if ($inSched) {
            if ($line -match '^\s*#') { continue }        # comment inside section
            if ($line -match '^\S') { break }              # next top-level key: leave section
            if ($line -match '^\s*time:\s*"?([0-9:]+)"?') { $schedTime = $Matches[1] }
            if ($line -match '^\s*interval_days:\s*(\d+)') { $schedDays = [int]$Matches[1] }
        }
    }
    Write-Output "config   : $cfgPath -> time=$schedTime interval_days=$schedDays"
} else {
    Write-Output "config   : not found, using defaults time=$schedTime interval_days=$schedDays"
}

$trigger = New-ScheduledTaskTrigger -Daily -At $schedTime -DaysInterval $schedDays

# StartWhenAvailable: catch up once after a missed window (machine was off)
$settingsParams = @{
    StartWhenAvailable         = $true
    AllowStartIfOnBatteries    = $true
    DontStopIfGoingOnBatteries = $true
    ExecutionTimeLimit         = (New-TimeSpan -Hours 1)
    MultipleInstances          = 'IgnoreNew'
    RestartCount               = 2
    RestartInterval            = (New-TimeSpan -Minutes 10)
}
$settings = New-ScheduledTaskSettingsSet @settingsParams

# Interactive = "run only when the user is logged on", so no password is stored
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

$description = ('Every {0} day(s) at {1} (from config.yaml): generate one AI news article and save it as a WeChat DRAFT (create_draft only, never mass send). Entry point: python main.py daily' -f $schedDays, $schedTime)

$registerParams = @{
    TaskName    = $taskName
    Action      = $action
    Trigger     = $trigger
    Settings    = $settings
    Principal   = $principal
    Description = $description
    Force       = $true
}
Register-ScheduledTask @registerParams | Out-Null

$info = Get-ScheduledTaskInfo -TaskName $taskName
Write-Output "registered: $taskName"
Write-Output ("state     : {0}" -f (Get-ScheduledTask -TaskName $taskName).State)
Write-Output ("next run  : {0}" -f $info.NextRunTime)
