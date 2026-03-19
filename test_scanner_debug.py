"""
Direct test of the scanner to see debug output
"""
import logging
from src.data_fetcher import DataFetcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

print("=" * 80)
print("TESTING DATA FETCHER - REAL DATA VERIFICATION")
print("=" * 80)

fetcher = DataFetcher()

# Test 1: Get single stock price
print("\n[TEST 1] Fetching current price for AAPL:")
print("-" * 80)
price_data = fetcher.get_current_price("AAPL")
print(f"\nResult: {price_data}\n")

# Test 2: Calculate momentum
print("[TEST 2] Calculating RSI momentum for AAPL:")
print("-" * 80)
momentum = fetcher.calculate_momentum("AAPL")
print(f"\nResult: RSI={momentum[0]:.2f}, Signal={momentum[1]}\n")

# Test 3: Scan a small industry
print("[TEST 3] Scanning AI industry (8 stocks):")
print("-" * 80)
results = fetcher.scan_industry("AI")
print(f"\nTop 5 by Buy Score:")
for i, stock in enumerate(results[:5], 1):
    print(f"{i}. {stock['ticker']:5s} | Price: ${stock['price']:8.2f} | RSI: {stock.get('rsi', 0):6.2f} | Buy: {stock['buy_score']} | Sell: {stock['sell_score']} | {stock['recommendation']}")

print("\n" + "=" * 80)
