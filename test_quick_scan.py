#!/usr/bin/env python
from src.data_fetcher import DataFetcher
from src.market_config import Market
import json

quick_result = DataFetcher.quick_scan_industry('AI', min_score=1.0, max_candidates=5, market=Market.US)
candidates = quick_result.get('candidates', [])
print(f'Candidates found: {len(candidates)}')
if candidates:
    print(f'\nFirst candidate:')
    print(f'  Ticker: {candidates[0].get("ticker")}')
    print(f'  RSI: {candidates[0].get("rsi")}')
    print(f'  RSI Status: {candidates[0].get("rsi_status")}')
    print(f'  Quick Score: {candidates[0].get("quick_score")}')
    print(f'  Reasons: {candidates[0].get("reasons")}')
else:
    print('No candidates found!')
    all_stocks = quick_result.get('all_stocks', [])
    if all_stocks:
        for stock in all_stocks[:3]:
            print(f"\nStock: {stock.get('ticker')}")
            print(f"  RSI: {stock.get('rsi')}")
            print(f"  RSI Status: {stock.get('rsi_status')}")
            print(f"  Quick Score: {stock.get('quick_score')}")
