@echo off
cd /d "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection"
start "paperb-iter05a_overnight" /belownormal /wait /b "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Scripts\python.exe" scripts\paperb\run_queue.py --config configs\iter05a_overnight.yaml --stop-at 07:30 >> "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\results\iter05a_pool\overnight\log.txt" 2>&1

