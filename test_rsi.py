#!/usr/bin/env python
from src.data_fetcher import DataFetcher
from src.market_config import Market

# Test calculate_momentum directly
print("Testing calculate_momentum...")
momentum = DataFetcher.calculate_momentum('MSFT')
print(f"MSFT Momentum: {momentum}")

# Test quick scan
print("\n\nTesting quick_scan_industry...")
quick_result = DataFetcher.quick_scan_industry('AI', min_score=1.0, max_candidates=5, market=Market.US)
candidates = quick_result.get('candidates', [])
print(f'Candidates found: {len(candidates)}')
if candidates:
    print(f'\nFirst candidate:')
    print(f'  Ticker: {candidates[0].get("ticker")}')
    print(f'  RSI: {candidates[0].get("rsi")}')
    print(f'  RSI Status: {candidates[0].get("rsi_status")}')
