import requests
import json
import time

print("Testing deep analysis by triggering manual scan via Flask API...")
url = "http://127.0.0.1:5000/api/scanner/scan-now/AI"

print(f"Calling: {url}")
try:
    response = requests.get(url, timeout=60)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Scan completed!")
        print(f"Results count: {data.get('results_count', 0)}")
        print(f"Execution details count: {len(data.get('execution_details', []))}")
        
        # Check first result
        results = data.get('results', [])
        if results:
            first = results[0]
            print(f"\nFirst ticker: {first.get('ticker')}")
            print(f"  Quick Score: {first.get('quick_score')}")
            print(f"  Deep Score: {first.get('deep_score', 'N/A')}")
            print(f"  Signal: {first.get('signal')}")
            print(f"  Recommendation: {first.get('recommendation')}")
            
        # Check execution details
        exec_details = data.get('execution_details', [])
        if exec_details:
            print(f"\nExecution Details:")
            for ed in exec_details[:3]:
                print(f"  - {ed.get('ticker')}: {ed.get('recommendation')} ({ed.get('status', 'unknown')})")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
