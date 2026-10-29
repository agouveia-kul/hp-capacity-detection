@echo off
rem 06 full run (configs\iter06.yaml), started detached by the agent on Alex's request (2026-10-26; relaunched 2026-10-29 with the
rem TabPFN cap at 2 and --retry-failed); no scheduled task is registered.
rem Below-normal priority is set by the launching process (inherited by the workers); 6 workers x 3 threads (queue config).
rem Resumable: running this file again skips finished jobs. Extra arguments (e.g. --retry-failed) are passed to the queue.
cd /d "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection"
set "TABPFN_MODEL_CACHE_DIR=C:\tabpfn_cache"
"C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Scripts\python.exe" scripts\paperb\run_queue.py --config configs\iter06.yaml --workers 6 %* >> "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\results\iter06_hybrid_ladder\log.txt" 2>&1
