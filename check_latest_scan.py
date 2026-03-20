import json
from pathlib import Path

# Check if new scan results have been generated with deep analysis
files = sorted(Path('scan_results').glob('us_*_scan.json'), key=lambda f: f.stat().st_mtime, reverse=True)

if files:
    latest = files[0]
    print(f"Latest scan file: {latest.name}")
    print(f"Modified: {latest.stat().st_mtime}")
    
    data = json.load(open(latest))
    print(f"\nFile structure keys: {list(data.keys())}")
    print(f"Results count: {len(data.get('results', []))}")
    print(f"Has execution_details: {'execution_details' in data}")
    
    if data.get('results'):
        r = data['results'][0]
        print(f"\nFirst result ({r.get('ticker')}):")
        print(f"  - quick_score: {r.get('quick_score', 'N/A')}")
        print(f"  - deep_score: {r.get('deep_score', 'N/A')}")
        print(f"  - signal: {r.get('signal', 'N/A')}")
        print(f"  - recommendation: {r.get('recommendation', 'N/A')}")
        
    if data.get('execution_details'):
        print(f"\nExecution details ({len(data['execution_details'])} entries):")
        for ed in data['execution_details'][:2]:
            print(f"  - {ed.get('ticker')}: {ed.get('recommendation')} ({ed.get('status', 'N/A')})")
else:
    print("No scan results found yet")
