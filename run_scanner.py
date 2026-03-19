#!/usr/bin/env python3
"""Start the background scanner to refresh all scan results"""

import logging
import time
from src.background_scanner import BackgroundScanner
from src.data_fetcher import DataFetcher, Market
from src.config import Settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

logger.info("\n" + "="*80)
logger.info("STARTING BACKGROUND SCANNER")
logger.info("="*80 + "\n")

config = Settings()
data_fetcher = DataFetcher()
scanner = BackgroundScanner()

try:
    # Start the scanner
    logger.info("🚀 Starting scanner thread...")
    scanner.start(data_fetcher, Market.US)
    
    # Wait for all scans to complete (gives it up to 5 minutes)
    logger.info("\n⏳ Waiting for scans to complete...")
    for i in range(600):  # 600 x 1 second = 10 minutes
        if not scanner.is_running:
            logger.info("\n✅ Scanner finished!")
            break
        time.sleep(1)
        if (i + 1) % 60 == 0:
            logger.info(f"   Still running... ({(i+1)//60} minutes elapsed)")
    
    # Display results summary
    logger.info("\n📊 SCAN RESULTS SUMMARY:")
    logger.info("="*80)
    
    results = scanner.scan_results
    for industry, stocks in results.items():
        count = len(stocks)
        buy_count = sum(1 for s in stocks if s.get('buy_score', 0) > 0)
        sell_count = sum(1 for s in stocks if s.get('sell_score', 0) > 0)
        logger.info(f"\n{industry:12s}: {count:3d} stocks | BUY: {buy_count:2d} | SELL: {sell_count:2d}")
        for stock in stocks[:3]:
            logger.info(f"  ├─ {stock['ticker']:6s}: {stock['recommendation']:4s} (buy={stock.get('buy_score')}, sell={stock.get('sell_score')})")
        if count > 3:
            logger.info(f"  └─ ... and {count-3} more stocks")

except KeyboardInterrupt:
    logger.info("\n⏹ Scanner interrupted by user")
except Exception as e:
    logger.exception(f"Error running scanner: {e}")
finally:
    logger.info("\n" + "="*80)
    logger.info("BACKGROUND SCANNER TEST COMPLETE")
    logger.info("="*80)
