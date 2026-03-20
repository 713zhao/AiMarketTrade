import json

d = json.load(open('scan_results/us_AI_scan.json'))
print(f'Total results: {len(d.get("results", []))}')
print(f'Execution details: {len(d.get("execution_details", []))}')
print(f'Timestamp: {d.get("timestamp")}')

# Show results structure
if d.get('results'):
    print(f"\nFirst result keys: {list(d['results'][0].keys())}")
else:
    print("No results in file")
