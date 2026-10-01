# Queue status: iter05b_quick

Session wall time 0.37 h; done 13, failed 9, remaining 0 (of 22).

| arm | done | failed | remaining | job hours (sum) | first start | last end |
|---|---|---|---|---|---|---|
| q_arm1 | 0 | 9 | 0 | 0.00 | - | - |
| q_arm2 | 9 | 0 | 0 | 0.86 | 2026-10-01T14:51:44 | 2026-10-01T15:12:06 |
| q_oracle | 2 | 0 | 0 | 0.07 | 2026-10-01T14:56:59 | 2026-10-01T15:00:30 |
| q_scale | 1 | 0 | 0 | 0.04 | 2026-10-01T14:59:38 | 2026-10-01T15:01:59 |
| q_bstar_o1b | 1 | 0 | 0 | 0.01 | 2026-10-01T15:00:12 | 2026-10-01T15:00:55 |

## FAILED q_arm1__s0__d0__n62__physics
```
concurrent.futures.process._RemoteTraceback: 
"""
Traceback (most recent call last):
  File "C:\Program Files\Python312\Lib\concurrent\futures\process.py", line 264, in _process_worker
    r = call_item.fn(*call_item.args, **call_item.kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_queue.py", line 102, in run_job
    res = getattr(importlib.import_module(mod), fn)(cfg, job["seed"])
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_benchmark.py", line 410, in run_seed
    "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines,
                                                                           ^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 382, in concat
    op = _Concatenator(
         ^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 445, in __init__
    objs, keys = self._clean_keys_and_objs(objs, keys)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 507, in _clean_keys_and_objs
    raise ValueError("No objects to concatenate")
```

## FAILED q_arm1__s0__d0__n62__linear
```
concurrent.futures.process._RemoteTraceback: 
"""
Traceback (most recent call last):
  File "C:\Program Files\Python312\Lib\concurrent\futures\process.py", line 264, in _process_worker
    r = call_item.fn(*call_item.args, **call_item.kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_queue.py", line 102, in run_job
    res = getattr(importlib.import_module(mod), fn)(cfg, job["seed"])
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_benchmark.py", line 410, in run_seed
    "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines,
                                                                           ^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 382, in concat
    op = _Concatenator(
         ^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 445, in __init__
    objs, keys = self._clean_keys_and_objs(objs, keys)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 507, in _clean_keys_and_objs
    raise ValueError("No objects to concatenate")
```

## FAILED q_arm1__s0__d0__n62__trees
```
concurrent.futures.process._RemoteTraceback: 
"""
Traceback (most recent call last):
  File "C:\Program Files\Python312\Lib\concurrent\futures\process.py", line 264, in _process_worker
    r = call_item.fn(*call_item.args, **call_item.kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_queue.py", line 102, in run_job
    res = getattr(importlib.import_module(mod), fn)(cfg, job["seed"])
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_benchmark.py", line 410, in run_seed
    "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines,
                                                                           ^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 382, in concat
    op = _Concatenator(
         ^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 445, in __init__
    objs, keys = self._clean_keys_and_objs(objs, keys)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 507, in _clean_keys_and_objs
    raise ValueError("No objects to concatenate")
```

## FAILED q_arm1__s0__d0__n62__kernel
```
concurrent.futures.process._RemoteTraceback: 
"""
Traceback (most recent call last):
  File "C:\Program Files\Python312\Lib\concurrent\futures\process.py", line 264, in _process_worker
    r = call_item.fn(*call_item.args, **call_item.kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_queue.py", line 102, in run_job
    res = getattr(importlib.import_module(mod), fn)(cfg, job["seed"])
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_benchmark.py", line 410, in run_seed
    "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines,
                                                                           ^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 382, in concat
    op = _Concatenator(
         ^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 445, in __init__
    objs, keys = self._clean_keys_and_objs(objs, keys)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 507, in _clean_keys_and_objs
    raise ValueError("No objects to concatenate")
```

## FAILED q_arm1__s0__d0__n62__catboost
```
concurrent.futures.process._RemoteTraceback: 
"""
Traceback (most recent call last):
  File "C:\Program Files\Python312\Lib\concurrent\futures\process.py", line 264, in _process_worker
    r = call_item.fn(*call_item.args, **call_item.kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_queue.py", line 102, in run_job
    res = getattr(importlib.import_module(mod), fn)(cfg, job["seed"])
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_benchmark.py", line 410, in run_seed
    "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines,
                                                                           ^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 382, in concat
    op = _Concatenator(
         ^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 445, in __init__
    objs, keys = self._clean_keys_and_objs(objs, keys)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 507, in _clean_keys_and_objs
    raise ValueError("No objects to concatenate")
```

## FAILED q_arm1__s0__d0__n62__neural
```
concurrent.futures.process._RemoteTraceback: 
"""
Traceback (most recent call last):
  File "C:\Program Files\Python312\Lib\concurrent\futures\process.py", line 264, in _process_worker
    r = call_item.fn(*call_item.args, **call_item.kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_queue.py", line 102, in run_job
    res = getattr(importlib.import_module(mod), fn)(cfg, job["seed"])
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_benchmark.py", line 410, in run_seed
    "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines,
                                                                           ^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 382, in concat
    op = _Concatenator(
         ^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 445, in __init__
    objs, keys = self._clean_keys_and_objs(objs, keys)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 507, in _clean_keys_and_objs
    raise ValueError("No objects to concatenate")
```

## FAILED q_arm1__s0__d0__n62__rawseries
```
concurrent.futures.process._RemoteTraceback: 
"""
Traceback (most recent call last):
  File "C:\Program Files\Python312\Lib\concurrent\futures\process.py", line 264, in _process_worker
    r = call_item.fn(*call_item.args, **call_item.kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_queue.py", line 102, in run_job
    res = getattr(importlib.import_module(mod), fn)(cfg, job["seed"])
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_benchmark.py", line 410, in run_seed
    "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines,
                                                                           ^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 382, in concat
    op = _Concatenator(
         ^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 445, in __init__
    objs, keys = self._clean_keys_and_objs(objs, keys)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 507, in _clean_keys_and_objs
    raise ValueError("No objects to concatenate")
```

## FAILED q_arm1__s0__d0__n62__tabpfn
```
concurrent.futures.process._RemoteTraceback: 
"""
Traceback (most recent call last):
  File "C:\Program Files\Python312\Lib\concurrent\futures\process.py", line 264, in _process_worker
    r = call_item.fn(*call_item.args, **call_item.kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_queue.py", line 102, in run_job
    res = getattr(importlib.import_module(mod), fn)(cfg, job["seed"])
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_benchmark.py", line 410, in run_seed
    "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines,
                                                                           ^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 382, in concat
    op = _Concatenator(
         ^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 445, in __init__
    objs, keys = self._clean_keys_and_objs(objs, keys)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 507, in _clean_keys_and_objs
    raise ValueError("No objects to concatenate")
```

## FAILED q_arm1__s0__d0__n62__gp
```
concurrent.futures.process._RemoteTraceback: 
"""
Traceback (most recent call last):
  File "C:\Program Files\Python312\Lib\concurrent\futures\process.py", line 264, in _process_worker
    r = call_item.fn(*call_item.args, **call_item.kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_queue.py", line 102, in run_job
    res = getattr(importlib.import_module(mod), fn)(cfg, job["seed"])
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\scripts\paperb\run_benchmark.py", line 410, in run_seed
    "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines,
                                                                           ^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 382, in concat
    op = _Concatenator(
         ^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 445, in __init__
    objs, keys = self._clean_keys_and_objs(objs, keys)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\VENANCIA\OneDrive - VITO\Desktop\hp-capacity-detection\.venv\Lib\site-packages\pandas\core\reshape\concat.py", line 507, in _clean_keys_and_objs
    raise ValueError("No objects to concatenate")
```
