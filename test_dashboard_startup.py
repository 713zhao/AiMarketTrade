"""Test the web dashboard startup to identify issues"""
import sys
import logging
from datetime import datetime

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("Testing Dashboard Startup")
logger.info("=" * 60)

try:
    logger.info("Starting imports...")
    from src.state import DeerflowState
    logger.info("✓ state imported")
    
    from src.market_config import Market, get_market_tickers, is_market_open
    logger.info("✓ market_config imported")
    
    from src.background_scanner import get_scanner
    logger.info("✓ background_scanner imported")
    
    from src.data_fetcher import DataFetcher
    logger.info("✓ data_fetcher imported")
    
    logger.info("\nChecking market status...")
    for market in [Market.US, Market.CHINA, Market.HONGKONG]:
        is_open = is_market_open(market)
        logger.info(f"  {market.value}: {'OPEN' if is_open else 'CLOSED'}")
    
    logger.info("\nTesting get_market_tickers...")
    tickers = get_market_tickers(Market.US)
    logger.info(f"✓ Got {len(tickers)} tickers for US market")
    
    logger.info("\nTesting DataFetcher...")
    data_fetcher = DataFetcher()
    logger.info("✓ DataFetcher initialized")
    
    logger.info("\nTesting Scanner initialization...")
    scanner = get_scanner()
    logger.info(f"✓ Scanner created: {type(scanner).__name__}")
    
    logger.info("\nCreating DeerflowState...")
    trading_state = DeerflowState(
        tickers=tickers[:5],
        trading_enabled=True,
        cash_balance=100000.0,
        positions={},
        executed_trades=[],
        portfolio_metrics={},
        trading_config={"position_size_pct": 0.10}
    )
    logger.info(f"✓ Trading state created with {len(tickers[:5])} tickers")
    
    logger.info("\nTesting Flask initialization...")
    from flask import Flask
    app = Flask(__name__)
    logger.info("✓ Flask app created")
    
    logger.info("\n" + "=" * 60)
    logger.info("SUCCESS: All components initialized!")
    logger.info("=" * 60)
    
except Exception as e:
    logger.error(f"\n✗ ERROR: {e}", exc_info=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
