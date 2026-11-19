@echo off
rem 08 queue, to be started detached only on Alex's request; no scheduled task is registered.
rem Usage: launch_detached.cmd <config> [queue args]. Resumable: running it again skips finished jobs. Log: results\iter08_change_detection\log.txt.
cd /d "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection"
set "TABPFN_MODEL_CACHE_DIR=C:\tabpfn_cache"
"C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Scripts\python.exe" scripts\paperb\run_queue.py --config %* >> "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\results\iter08_change_detection\log.txt" 2>&1
