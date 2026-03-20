import json
import os
from pathlib import Path

files = sorted(Path('scan_results').glob('*.json'), key=os.path.getmtime, reverse=True)[:3]
for f in files:
    data = json.load(open(f))
    print(f'\n=== {f.name} ===')
    print(f'Timestamp: {data.get("timestamp", "N/A")}')
    print(f'Results count: {len(data.get("results", []))}')
    print(f'Has execution_details: {"execution_details" in data}')
    
    if data.get('results'):
        print(f'First few tickers:')
        for r in data['results'][:3]:
            print(f"  - {r['ticker']}: signal={r.get('quick_signal', 'N/A')}, deep_score={r.get('deep_score', 'N/A')}")
    
    if 'execution_details' in data and data['execution_details']:
        print(f'Execution details count: {len(data["execution_details"])}')
        for ed in data['execution_details'][:2]:
            print(f"  - {ed.get('ticker')}: {ed.get('recommendation')} ({ed.get('status')})")
    else:
        print('No execution_details in this file')
