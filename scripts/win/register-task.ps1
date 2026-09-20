# Register/update the "create one WeChat draft" scheduled task.
#
#   Every 2 days at 08:00 -> python main.py daily (create_draft only, never
#   publish_draft / mass send -- see AGENTS.md).
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

# Every 2 days at 08:00 -- mirrors config.yaml scheduler.time / interval_days
$trigger = New-ScheduledTaskTrigger -Daily -At '08:00' -DaysInterval 2

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

$description = 'Every 2 days 08:00: generate one AI news article and save it as a WeChat DRAFT (create_draft only, never mass send). Entry point: python main.py daily'

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
