"""
Background stock scanner that runs periodically to identify trading opportunities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Thread, Lock
import time
import json
from pathlib import Path
from src.market_config import Market, get_all_industries, is_market_open

logger = logging.getLogger(__name__)


class BackgroundScanner:
    """Manages background stock scanning"""
    
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.lock = Lock()
        self.scan_results = {}  # {industry: [results]}
        self.last_scan_time = {}  # {industry: timestamp}
        self.scan_interval = 300  # 5 minutes in seconds
        self.market = Market.US  # Default market
        self.enabled_industries = []  # Will be set dynamically by market
        self.data_fetcher = None  # Will be set by start()
        
        # Set up results directory
        self.results_dir = Path("scan_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def start(self, data_fetcher, market: Market = Market.US):
        """
        Start the background scanner
        
        Args:
            data_fetcher: DataFetcher instance for scanning
            market: Market to scan (default: Market.US)
        """
        if self.is_running:
            logger.warning(f"Scanner already running. Updating market to {market.value}")
            # Allow updating market even if already running
            self.market = market
            self.enabled_industries = get_all_industries(market)
            if data_fetcher:
                self.data_fetcher = data_fetcher
            return
        
        # Initialize scanner
        self.market = market
        self.enabled_industries = get_all_industries(market)
        self.is_running = True
        self.data_fetcher = data_fetcher
        
        logger.info(f"Initializing background scanner:")
        logger.info(f"  Market: {market.value}")
        logger.info(f"  Industries: {', '.join(self.enabled_industries)}")
        logger.info(f"  Data Fetcher: {type(data_fetcher).__name__}")
        
        # Start scanner thread
        self.thread = Thread(target=self._scan_loop, daemon=True)
        self.thread.start()
        logger.info(f"✓ Background scanner thread started")
    
    def stop(self):
        """Stop the background scanner"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background scanner stopped")
    
    def _scan_loop(self):
        """Main scan loop running in background thread"""
        while self.is_running:
            try:
                # Verify data_fetcher is available
                if not self.data_fetcher:
                    logger.warning("Data fetcher not initialized. Waiting for setup...")
                    time.sleep(10)
                    continue
                
                # Check if market is open
                if not is_market_open(self.market):
                    logger.debug(f"Market {self.market.value} is closed. Scanning will resume during market hours.")
                    # Check every minute if market opened
                    time.sleep(60)
                    continue
                
                # Market is open - perform scans
                for industry in self.enabled_industries:
                    self._scan_industry(industry)
                
                # Wait before next scan cycle
                time.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                time.sleep(10)  # Wait before retrying
    
    def _save_results_to_file(self, industry: str, results: List[Dict]):
        """Save scan results to JSON file with market-specific naming"""
        try:
            # Include market name in filename to avoid conflicts when multiple markets scan
            market_prefix = self.market.value.lower()
            file_path = self.results_dir / f"{market_prefix}_{industry}_scan.json"
            with open(file_path, 'w') as f:
                json.dump({
                    "industry": industry,
                    "market": self.market.value,
                    "timestamp": datetime.now().isoformat(),
                    "results": results
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving results for {industry}: {e}")
    
    def _format_as_markdown_table(self, industry: str, results: List[Dict]) -> str:
        """Format scan results as markdown table"""
        if not results:
            return f"### {industry} Industry Scan Results\n\nNo results found.\n"
        
        table = f"### {industry} Industry Scan Results\n\n"
        table += "| Ticker | Price | RSI | Status | Signal | Reason |\n"
        table += "|--------|-------|-----|--------|--------|--------|\n"
        
        for r in results:
            ticker = r.get("ticker", "N/A")
            price = f"${r.get('price', 0):.2f}"
            rsi = f"{r.get('rsi', 0):.2f}"
            status = r.get("rsi_status", "N/A")
            signal = r.get("recommendation", "HOLD")
            reason = r.get("reason", "No signals")
            
            # Highlight BUY/SELL signals
            if signal == "SELL":
                signal = f"**{signal}** 🔴"
            elif signal == "BUY":
                signal = f"**{signal}** 🟢"
            
            table += f"| {ticker} | {price} | {rsi} | {status} | {signal} | {reason} |\n"
        
        return table
    
    def _scan_industry(self, industry: str):
        """Scan a single industry"""
        try:
            # Verify data_fetcher is available
            if not self.data_fetcher:
                logger.error(f"Cannot scan {industry}: data_fetcher not initialized")
                return
            
            logger.info(f"\n🚀 Starting scan for {industry} ({self.market.value} market)...")
            
            # Call scan_industry with explicit market parameter
            results = self.data_fetcher.scan_industry(industry, self.market)
            
            if not results:
                logger.warning(f"No results returned for {industry}")
                results = []
            
            with self.lock:
                self.scan_results[industry] = results
                self.last_scan_time[industry] = datetime.now().isoformat()
            
            # Save to file for persistence
            self._save_results_to_file(industry, results)
            
            # Format and print markdown table
            table = self._format_as_markdown_table(industry, results)
            logger.info("\n" + table)
            
            # Summary statistics
            buy_count = len([r for r in results if r.get("recommendation") == "BUY"])
            sell_count = len([r for r in results if r.get("recommendation") == "SELL"])
            hold_count = len([r for r in results if r.get("recommendation") == "HOLD"])
            
            logger.info(f"✓ {industry} scan complete:")
            logger.info(f"  │ Total stocks: {len(results)}")
            logger.info(f"  ├─ 🟢 BUY signals: {buy_count}")
            logger.info(f"  ├─ 🔴 SELL signals: {sell_count}")
            logger.info(f"  └─ ⚪ HOLD: {hold_count}\n")
            
        except Exception as e:
            logger.error(f"✗ Error scanning {industry}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def get_results(self, industry: Optional[str] = None) -> Dict:
        """Get scan results"""
        with self.lock:
            if industry:
                return {
                    "industry": industry,
                    "results": self.scan_results.get(industry, []),
                    "last_updated": self.last_scan_time.get(industry),
                }
            else:
                return {
                    "results": self.scan_results,
                    "last_updated": self.last_scan_time,
                }
    
    def get_recommendations(self, industry: str, signal_type: str = "BUY", min_score: int = 2) -> List[Dict]:
        """Get stocks with specific signal recommendation"""
        with self.lock:
            results = self.scan_results.get(industry, [])
        
        if signal_type == "BUY":
            filtered = [r for r in results if r.get("recommendation") == "BUY" and r.get("buy_score", 0) >= min_score]
        elif signal_type == "SELL":
            filtered = [r for r in results if r.get("recommendation") == "SELL" and r.get("sell_score", 0) >= min_score]
        else:
            filtered = [r for r in results if r.get("recommendation") == "HOLD"]
        
        return sorted(filtered, key=lambda x: x.get("buy_score" if signal_type == "BUY" else "sell_score", 0), reverse=True)
    
    def get_all_results(self, industry: str) -> List[Dict]:
        """Get ALL scan results for an industry without any filtering"""
        with self.lock:
            results = self.scan_results.get(industry, [])
        
        # If no results in memory, try loading from file
        if not results:
            results = self.load_results_from_file(industry) or []
        
        return results
    
    def set_results(self, industry: str, results: List[Dict]):
        """Manually set scan results for an industry (used by web API for immediate results)"""
        with self.lock:
            self.scan_results[industry] = results
            self.last_scan_time[industry] = datetime.now().isoformat()
        
        # Save to file
        self._save_results_to_file(industry, results)
        # Print formatted table
        table = self._format_as_markdown_table(industry, results)
        logger.info("\n" + table)
        logger.info(f"Results updated for {industry}: {len(results)} confirmed picks")
    
    def get_scan_table(self, industry: Optional[str] = None) -> str:
        """Get formatted markdown table of scan results"""
        if industry:
            with self.lock:
                results = self.scan_results.get(industry, [])
            return self._format_as_markdown_table(industry, results)
        else:
            # Return all tables
            all_tables = ""
            for ind in self.enabled_industries:
                with self.lock:
                    results = self.scan_results.get(ind, [])
                all_tables += self._format_as_markdown_table(ind, results) + "\n"
            return all_tables
    
    def load_results_from_file(self, industry: str) -> Optional[List[Dict]]:
        """Load scan results from file"""
        try:
            file_path = self.results_dir / f"{industry}_scan.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return data.get("results", [])
        except Exception as e:
            logger.error(f"Error loading results for {industry}: {e}")
        return None
    
    def set_enabled_industries(self, industries: List[str]):
        """Set which industries to scan"""
        self.enabled_industries = industries
        logger.info(f"Enabled industries: {industries}")
    
    def force_scan(self, industry: str):
        """Force a scan on a specific industry immediately"""
        self._scan_industry(industry)
    
    def get_status(self) -> Dict:
        """Get scanner status"""
        return {
            "running": self.is_running,
            "scan_interval": self.scan_interval,
            "enabled_industries": self.enabled_industries,
            "last_scans": self.last_scan_time,
            "total_results": len(self.scan_results),
        }


# Global scanner instance
_scanner_instance = None
_scanner_lock = Lock()


def get_scanner() -> BackgroundScanner:
    """Get or create the global scanner instance"""
    global _scanner_instance
    with _scanner_lock:
        if _scanner_instance is None:
            _scanner_instance = BackgroundScanner()
        return _scanner_instance
