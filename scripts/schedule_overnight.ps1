<#
.SYNOPSIS
  Register a one-off Windows Task Scheduler task that runs the Paper B job queue overnight (iteration 05a, Task 4b).

.DESCRIPTION
  Writes <out_dir>\launch.cmd (cd to the repository, start the queue with .venv\Scripts\python at below-normal priority,
  append stdout and stderr to <out_dir>\log.txt) and registers the task "paperb-<exp_id>" for the current user, once,
  at -StartAt (today, or tomorrow if that time has passed). The task runs only while the user is logged on (no password
  is stored) and needs no admin rights. The same schedule as `schtasks /Create /SC ONCE /ST <StartAt> /TN "paperb-<exp_id>"`,
  registered through the ScheduledTasks cmdlets so the start date does not depend on the locale's date format.
  The queue keeps the PC awake while it runs (SetThreadExecutionState); the PC must be awake at -StartAt.
  Pausing OneDrive sync overnight is advised. -DryRun prints what would be registered and changes nothing.
  -Continuous (05b, A6) omits the morning stop: the queue also runs in the daytime, at below-normal priority, until no job remains.
  -Shard I/N (05b) runs only the jobs at positions I mod N, so several machines can share one queue (see run_queue.py).
  -Families a,b (05b) runs only those queue families, e.g. rawseries,tabpfn on the GPU machine.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\schedule_overnight.ps1 -Config configs\iter05a_overnight.yaml -StopAt 07:30
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\schedule_overnight.ps1 -Config configs\iter05b_stage1.yaml -StartAt 22:00 -Continuous
#>
param(
    [Parameter(Mandatory = $true)][string]$Config,
    [string]$StartAt = "22:00",
    [string]$StopAt = "",
    [int]$Workers = 0,
    [string]$Shard = "",
    [string]$Families = "",
    [switch]$Continuous,
    [switch]$DryRun
)
if ($Continuous -and $StopAt) { throw "-Continuous runs until the queue is empty: do not combine it with -StopAt" }
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$yaml = Get-Content (Join-Path $Repo $Config) -Raw
$ExpId = ([regex]::Match($yaml, '(?m)^exp_id:\s*(\S+)')).Groups[1].Value
$OutDir = Join-Path $Repo ([regex]::Match($yaml, '(?m)^out_dir:\s*(\S+)')).Groups[1].Value
if (-not $ExpId -or -not $OutDir) { throw "exp_id / out_dir not found in $Config" }

$QueueArgs = "--config $Config"
if ($StopAt -and -not $Continuous) { $QueueArgs += " --stop-at $StopAt" }
if ($Workers -gt 0) { $QueueArgs += " --workers $Workers" }
if ($Shard) { $QueueArgs += " --shard $Shard" }
if ($Families) { $QueueArgs += " --families $Families" }
$Launch = Join-Path $OutDir "launch.cmd"
$Body = "@echo off`r`ncd /d `"$Repo`"`r`nstart `"paperb-$ExpId`" /belownormal /wait /b `"$Repo\.venv\Scripts\python.exe`" scripts\paperb\run_queue.py $QueueArgs >> `"$OutDir\log.txt`" 2>&1`r`n"

$At = [datetime]::ParseExact($StartAt, "HH:mm", $null)
if ($At -le (Get-Date)) { $At = $At.AddDays(1) }
$TaskName = "paperb-$ExpId"
$Mode = if ($Continuous) { "continuous until the queue is empty (day and night)" } elseif ($StopAt) { "no new job after $StopAt" } else { "until the queue is empty" }
Write-Output "Task      : $TaskName (current user, once at $($At.ToString('yyyy-MM-dd HH:mm')), below-normal priority, $Mode)"
Write-Output "Launcher  : $Launch"
Write-Output "Command   : .venv\Scripts\python.exe scripts\paperb\run_queue.py $QueueArgs >> $OutDir\log.txt"
if ($DryRun) { Write-Output "DryRun: nothing written or registered."; exit 0 }

New-Item -ItemType Directory -Force $OutDir | Out-Null
Set-Content -Path $Launch -Value $Body -Encoding ASCII
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$Launch`""
$Trigger = New-ScheduledTaskTrigger -Once -At $At
$Settings = New-ScheduledTaskSettingsSet -Priority 7 -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
Write-Output "Registered $TaskName. Check: Get-ScheduledTask -TaskName $TaskName ; remove: Unregister-ScheduledTask -TaskName $TaskName"
