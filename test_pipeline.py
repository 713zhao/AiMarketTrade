#!/usr/bin/env python
from src.data_fetcher import DataFetcher
from src.market_config import Market
from src.config import Settings

# Test quick scan
print("Testing quick_scan_industry...")
quick_result = DataFetcher.quick_scan_industry('AI', market=Market.US)
quick_results = quick_result.get('candidates', [])
print(f'Quick candidates found: {len(quick_results)}')

for candidate in quick_results[:2]:
    print(f"\n{candidate['ticker']}:")
    print(f"  Quick Score: {candidate['quick_score']}")
    print(f"  Quick Signal: {candidate['quick_signal']}")
    print(f"  RSI: {candidate['rsi']}")
    print(f"  RSI Status: {candidate['rsi_status']}")

# Now test if they would pass deep analysis validation
print("\n\nChecking thresholds...")
config = Settings()
print(f"Quick scan min score: {config.quick_scan_min_score}")
print(f"Deep analysis min score: {config.deep_analysis_min_score}")
print(f"Deep analysis require agreement: {config.deep_analysis_require_agreement}")
print(f"Deep analysis max score diff: {config.deep_analysis_max_score_diff}")
