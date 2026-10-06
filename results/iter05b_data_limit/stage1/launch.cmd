@echo off
cd /d "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection"
start "paperb-iter05b_stage1" /belownormal /wait /b "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Scripts\python.exe" scripts\paperb\run_queue.py --config configs\iter05b_stage1.yaml --workers 6 --families physics,linear,trees,kernel,neural >> "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\results\iter05b_data_limit\stage1\log.txt" 2>&1

