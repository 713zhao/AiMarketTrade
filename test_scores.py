#!/usr/bin/env python
from src.data_fetcher import DataFetcher
from src.market_config import Market
from src.config import Settings

# Test quick scan with different min_scores
config = Settings()
print(f"Quick scan min score setting: {config.quick_scan_min_score}")

for min_score in [1.0, 2.0, 3.0]:
    print(f"\n\nTesting with min_score={min_score}...")
    quick_result = DataFetcher.quick_scan_industry('AI', min_score=min_score, market=Market.US)
    quick_results = quick_result.get('candidates', [])
    print(f'Candidates found: {len(quick_results)}')
    
    # Show first few
    for candidate in quick_results[:3]:
        print(f"  {candidate['ticker']:6s} score={candidate['quick_score']:.1f} signal={candidate['quick_signal']}")
