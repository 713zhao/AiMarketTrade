#!/usr/bin/env python
from src.data_fetcher import DataFetcher
from web_dashboard_trading import deep_analysis_candidates
from src.market_config import Market
from src.config import Settings

config = Settings()
print(f"Quick scan min score: {config.quick_scan_min_score}")
print(f"Deep analysis min score: {config.deep_analysis_min_score}")
print(f"Deep analysis max score diff: {config.deep_analysis_max_score_diff}")
print(f"Deep analysis require agreement: {config.deep_analysis_require_agreement}")

# Get candidates from quick scan
print("\n\nGetting quick scan candidates...")
quick_result = DataFetcher.quick_scan_industry('AI', market=Market.US)
quick_results = quick_result.get('candidates', [])
print(f"Quick candidates: {len(quick_results)}")

for candidate in quick_results:
    print(f"  {candidate['ticker']:6s} score={candidate['quick_score']:.1f} signal={candidate['quick_signal']} rsi={candidate['rsi']}")

# Run deep analysis
print(f"\n\nRunning deep analysis on {len(quick_results)} candidates...")
validated_results = deep_analysis_candidates(quick_results, 'AI', config)
print(f"Validated (confirmed) results: {len(validated_results)}")

for result in validated_results:
    print(f"  {result['ticker']:6s} deep_score={result['deep_score']:.1f} signal={result['recommendation']}")
