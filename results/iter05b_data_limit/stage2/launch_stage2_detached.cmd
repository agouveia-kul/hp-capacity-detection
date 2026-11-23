@echo off
rem 05b Stage 2 full run, started detached by the agent on Alex's request (2026-10-08); same queue as the scheduled-task launch.
cd /d "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection"
set "TABPFN_MODEL_CACHE_DIR=C:\tabpfn_cache"
"C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Scripts\python.exe" scripts\paperb\run_queue.py --config configs\iter05b_stage2.yaml --workers 6 >> "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\results\iter05b_data_limit\stage2\log.txt" 2>&1
