import json
from pathlib import Path

print("CHECKING DEEP ANALYSIS STATUS ACROSS ALL INDUSTRIES")
print("=" * 80)

files = list(Path('scan_results').glob('us_*_scan.json'))

for file in sorted(files):
    data = json.load(open(file))
    industry = data.get('industry', file.stem)
    results = data.get('results', [])
    
    if not results:
        print(f"\n{industry:12} - No results (may not have passed filter)")
        continue
    
    # Count recommendations
    buys = len([r for r in results if r.get('recommendation') == 'BUY'])
    sells = len([r for r in results if r.get('recommendation') == 'SELL'])
    
    # Check if deep_score exists
    has_deep_score = 'deep_score' in results[0] if results else False
    
    recommendation = "✓ GOOD" if has_deep_score and results else "✗ Check"
    print(f"{industry:12} - {len(results):2} results | {buys} BUY, {sells} SELL | Deep analysis: {recommendation}")
    
    # Show first ticker if available
    if results:
        r = results[0]
        print(f"              First: {r.get('ticker')} ({r.get('recommendation')}, deep_score={r.get('deep_score', 'N/A')})")

print("\n" + "=" * 80)
print("All industries should show ✓ GOOD and have deep_score values")
