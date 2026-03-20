#!/usr/bin/env python
"""Check if background scanner is running and check execution details."""

import json
from pathlib import Path
from src.background_scanner import get_scanner

# Check scanner status
scanner = get_scanner()
status = scanner.get_status()

print("=" * 60)
print("BACKGROUND SCANNER STATUS")
print("=" * 60)
print(f"Running: {status['running']}")
print(f"Scan interval: {status['scan_interval']}s")
print(f"Enabled industries: {len(status['enabled_industries'])}")
print(f"Total results in memory: {status['total_results']}")
print(f"Last scans: {len(status['last_scans'])} industries")

# Check scan files
print("\n" + "=" * 60)
print("SCAN RESULT FILES")
print("=" * 60)
results_dir = Path('scan_results')
if results_dir.exists():
    files = sorted(results_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
    print(f"Found {len(files)} scan result files")
    
    if files:
        for file in files[:3]:  # Show latest 3 files
            print(f"\nFile: {file.name}")
            with open(file) as f:
                data = json.load(f)
                print(f"  - Results: {len(data.get('results', []))} items")
                has_exec = 'execution_details' in data
                print(f"  - Execution details: {has_exec}")
                if has_exec:
                    exec_details = data.get('execution_details', [])
                    executed = len([e for e in exec_details if e.get('executed')])
                    skipped = len(exec_details) - executed
                    print(f"    - Executed: {executed}, Skipped: {skipped}")
else:
    print('scan_results dir not found')

print("\n" + "=" * 60)
