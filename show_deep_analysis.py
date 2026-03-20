import json

d = json.load(open('scan_results/us_AI_scan.json'))
results = d.get('results', [])

print("=" * 80)
print(f"AI INDUSTRY SCAN RESULTS - {len(results)} tickers passed deep analysis")
print("=" * 80)

for r in results:
    ticker = r['ticker']
    quick_score = r.get('quick_score', 0)
    deep_score = r.get('deep_score', 0)
    signal = r.get('signal', 'HOLD')
    recommendation = r.get('recommendation', 'HOLD')
    price = r.get('price', 0)
    reason = r.get('reason', 'N/A')
    
    print(f"\n✓ {ticker}")
    print(f"  Price: ${price:.2f}")
    print(f"  Quick Score: {quick_score:.1f}/5")
    print(f"  Deep Score: {deep_score:.1f}/10")
    print(f"  Signal: {signal}")
    print(f"  Recommendation: {recommendation}")
    print(f"  RSI Status: {r.get('rsi_status', 'N/A')}")
    print(f"  Reason: {reason}")
    print(f"  Reasons: {', '.join(r.get('reasons', []))}")

print("\n" + "=" * 80)
print(f"Note: These {len(results)} tickers passed BOTH quick and deep analysis filters")
print(f"Configuration Thresholds:")
print(f"  - Quick scan minimum score: 2.0")
print(f"  - Deep analysis minimum score: 3.5/10")
print("=" * 80)
