@echo off
rem 07 queue, started detached by the agent on Alex's request (probe: 2026-11-17, "Paused, start probe"); no scheduled task is registered.
rem Usage: launch_detached.cmd <config> [queue args]. Resumable: running it again skips finished jobs. Log: results\iter07_transfer\log.txt.
cd /d "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection"
set "TABPFN_MODEL_CACHE_DIR=C:\tabpfn_cache"
"C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Scripts\python.exe" scripts\paperb\run_queue.py --config %* >> "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\results\iter07_transfer\log.txt" 2>&1
