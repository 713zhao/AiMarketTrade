import json
import time
from pathlib import Path

# Wait for background scanner to generate results (about 5 minutes)
print("Waiting for background scanner to generate new results with deep analysis...")
print("Note: Background scanner runs every 5 minutes")
print("Path: scan_results/")

for i in range(2):  # Wait up to 10 minutes in 5-minute intervals
    time.sleep(300)  # Wait 5 minutes
    
    files = list(Path('scan_results').glob('*.json'))
    if files:
        print(f"\n✓ Scan results generated at {files[0].stat().st_mtime}!")
        
        # Check first file for deep_score
        data = json.load(open(files[0]))
        if data.get('results'):
            first_result = data['results'][0]
            print(f"First ticker: {first_result.get('ticker')}")
            print(f"Has deep_score: {'deep_score' in first_result}")
            print(f"Deep score value: {first_result.get('deep_score', 'N/A')}")
            
            if 'execution_details' in data:
                print(f"Has execution_details: True ({len(data['execution_details'])} entries)")
                if data['execution_details']:
                    print(f"First execution detail: {data['execution_details'][0]}")
            else:
                print(f"Has execution_details: False")
        break
    else:
        print(f"Waiting for scan #{i+1}... No files yet")

print("Done!")
