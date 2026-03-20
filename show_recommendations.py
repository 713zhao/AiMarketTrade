import json
from pathlib import Path

print("\n" + "=" * 80)
print("LATEST DEEP ANALYSIS RECOMMENDATIONS - ALL INDUSTRIES")
print("=" * 80)

all_recommendations = {'BUY': [], 'SELL': []}

for file in Path('scan_results').glob('us_*_scan.json'):
    data = json.load(open(file))
    for result in data.get('results', []):
        rec = result.get('recommendation', 'HOLD')
        if rec in all_recommendations:
            all_recommendations[rec].append({
                'ticker': result.get('ticker'),
                'industry': data.get('industry'),
                'deep_score': result.get('deep_score', 0),
                'quick_score': result.get('quick_score', 0),
                'reason': result.get('reason', 'N/A'),
                'rsi_status': result.get('rsi_status', 'N/A'),
            })

print(f"\n🟢 BUY SIGNALS ({len(all_recommendations['BUY'])} tickers):")
for item in sorted(all_recommendations['BUY'], key=lambda x: x['deep_score'], reverse=True):
    print(f"  ✓ {item['ticker']:6} | {item['industry']:12} | Deep: {item['deep_score']:4.1f}/10 | RSI: {item['rsi_status']}")

print(f"\n🔴 SELL SIGNALS ({len(all_recommendations['SELL'])} tickers):")
for item in sorted(all_recommendations['SELL'], key=lambda x: x['deep_score'], reverse=True):
    print(f"  ✓ {item['ticker']:6} | {item['industry']:12} | Deep: {item['deep_score']:4.1f}/10 | RSI: {item['rsi_status']}")

print("\n" + "=" * 80)
print(f"Next scan cycle: Every ~5 minutes")
print("View dashboard: http://127.0.0.1:5000")
print("=" * 80 + "\n")
