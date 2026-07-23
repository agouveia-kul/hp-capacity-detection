import json
from pathlib import Path

path = Path(r'c:/Users/VENANCIA/OneDrive - VITO/Desktop/NILM/HeatPumpDetection_refactored.ipynb')
nb = json.loads(path.read_text(encoding='utf-8'))
errors = []
for idx, cell in enumerate(nb['cells'], 1):
    if cell.get('cell_type') != 'code':
        continue
    source = ''.join(cell.get('source', []))
    if not source.strip():
        continue
    try:
        compile(source, f'<cell {idx}>', 'exec')
    except Exception as exc:
        errors.append((idx, str(exc), source[:1200]))
        break

if errors:
    idx, exc, source_snippet = errors[0]
    print('ERRORS', idx, exc)
    print('SOURCE SNIPPET:')
    print(source_snippet)
else:
    print('Notebook syntax check passed for all code cells.')
