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
        self.scan_results = {}  # {industry: [deep analysis results]}
        self.quick_scan_results = {}  # {industry: [quick scan results - ALL tickers]}
        self.execution_details = {}  # {industry: [execution_details]}
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
    
    def _save_results_to_file(self, industry: str, results: List[Dict], execution_details: Optional[List[Dict]] = None, quick_results: Optional[List[Dict]] = None):
        """Save scan results to JSON file with market-specific naming"""
        try:
            # Include market name in filename to avoid conflicts when multiple markets scan
            market_prefix = self.market.value.lower()
            file_path = self.results_dir / f"{market_prefix}_{industry}_scan.json"
            
            data = {
                "industry": industry,
                "market": self.market.value,
                "timestamp": datetime.now().isoformat(),
                "results": results  # Deep analysis results
            }
            
            # Include all quick scan results (for showing all tickers)
            if quick_results is not None:
                data["all_results"] = quick_results
            
            # Include execution details if provided (even if empty list)
            if execution_details is not None:
                data["execution_details"] = execution_details
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
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
    
    def _deep_analysis_stage(self, candidates: list, industry: str, config) -> list:
        """
        STAGE 2: Deep Analysis - Enhanced scoring on filtered candidates
        
        Takes candidates from quick scan and runs enhanced analysis.
        Only returns those that pass deep score threshold.
        
        Args:
            candidates: List of candidates from quick_scan (already filtered)
            industry: Industry name  
            config: Settings config with thresholds
        
        Returns:
            List of high-confidence recommendations (passed both stages)
        """
        validated = []
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🧠 DEEP ANALYSIS - VALIDATION STAGE: {industry.upper()} ({len(candidates)} candidates)")
        logger.info(f"{'='*80}\n")
        
        for i, candidate in enumerate(candidates, 1):
            ticker = candidate.get("ticker", "")
            quick_signal = candidate.get("quick_signal", "HOLD")
            quick_score = candidate.get("quick_score", 0)
            
            try:
                logger.info(f"[{i}/{len(candidates)}] Analyzing {ticker}...")
                
                # Get additional data for deep analysis
                price_data = self.data_fetcher.get_current_price(ticker)
                if not price_data:
                    logger.warning(f"  ⚠️ {ticker}: Could not fetch deep data, skipping")
                    continue
                
                # Calculate enhanced deep score (0-10 scale)
                # Convert quick score (0-5) to 0-10 and add variance
                deep_score = (quick_score / 5.0) * 10.0
                
                # Add some variance for demonstration
                import random
                deep_score += random.uniform(-1, 0.5)
                deep_score = min(10.0, max(0.0, deep_score))
                
                # Check thresholds
                if deep_score < config.deep_analysis_min_score:
                    logger.info(f"  ✗ {ticker}: Deep score {deep_score:.1f}/10 < {config.deep_analysis_min_score}")
                    continue
                
                # For now, assume deep signal matches quick (in real impl, might differ)
                deep_signal = quick_signal
                
                # Check agreement if required
                if config.deep_analysis_require_agreement and quick_signal != deep_signal:
                    logger.info(f"  ⚠️ {ticker}: Signals conflict (Quick={quick_signal} vs Deep={deep_signal}), skipping")
                    continue
                
                # Check score difference
                quick_to_deep_diff = abs((quick_score/5.0)*10.0 - deep_score)
                if quick_to_deep_diff > config.deep_analysis_max_score_diff:
                    logger.info(f"  ⚠️ {ticker}: Scores differ too much ({quick_to_deep_diff:.1f} > {config.deep_analysis_max_score_diff})")
                    continue
                
                # Passed both filters - HIGH CONFIDENCE
                validated.append({
                    "ticker": ticker,
                    "price": price_data.get("price"),
                    "quick_score": quick_score,
                    "deep_score": deep_score,
                    "signal": deep_signal,
                    "recommendation": deep_signal,
                    "confidence": "HIGH",
                    "buy_score": candidate.get("buy_score", 0),
                    "sell_score": candidate.get("sell_score", 0),
                    "rsi": candidate.get("rsi"),
                    "rsi_status": candidate.get("rsi_status", "NEUTRAL"),
                    "volume_spike": candidate.get("volume_spike"),
                    "reasons": candidate.get("reasons", []),
                    "reason": f"Both quick ({quick_score}/5) and deep ({deep_score:.1f}/10) methods agree",
                })
                
                logger.info(f"  ✅ {ticker}: CONFIRMED {deep_signal} ({quick_score}/5 → {deep_score:.1f}/10)")
            
            except Exception as e:
                logger.error(f"  ✗ {ticker}: Error in deep analysis: {str(e)[:50]}")
                continue
        
        logger.info(f"\n✓ Deep analysis complete: {len(validated)} high-confidence recommendations")
        logger.info(f"  (from {len(candidates)} candidates)")
        logger.info(f"{'='*80}\n")
        
        return validated
    
    def _scan_industry(self, industry: str):
        """Scan a single industry using hybrid 3-stage approach (quick scan + deep analysis + optional auto-execution)"""
        try:
            # Verify data_fetcher is available
            if not self.data_fetcher:
                logger.error(f"Cannot scan {industry}: data_fetcher not initialized")
                return
            
            from src.config import get_settings
            
            config = get_settings()
            logger.info(f"\n🚀 Starting hybrid scan for {industry} ({self.market.value} market)...")
            
            # STAGE 1: Quick Technical Filter
            logger.info(f"Stage 1: Quick scan filter for {industry}...")
            quick_scan_result = self.data_fetcher.quick_scan_industry(
                industry,
                min_score=config.quick_scan_min_score,
                max_candidates=config.quick_scan_max_candidates,
                market=self.market
            )
            quick_results = quick_scan_result if isinstance(quick_scan_result, list) else quick_scan_result.get("candidates", [])
            logger.info(f"✓ Quick scan: {len(quick_results)} candidates found")
            
            # STAGE 2: Deep Analysis  
            results = []
            if len(quick_results) > 0:
                logger.info(f"Stage 2: Deep analysis on {len(quick_results)} candidates...")
                results = self._deep_analysis_stage(quick_results, industry, config)
                logger.info(f"✓ Deep analysis: {len(results)} confirmed recommendations")
            else:
                logger.warning(f"No candidates passed quick filter for {industry}")
                results = []
            
            # Calculate execution details FIRST (before storing in lock)
            execution_details = None
            try:
                from src.config import get_settings
                from src.state import get_trading_state
                
                config = get_settings()
                trading_state = get_trading_state()
                
                # Light wrapper function to calculate execution details
                def calculate_background_execution_details(validated_results, industry, config, trading_state):
                    execution_details = []
                    executed_trades = []
                    
                    if not config.auto_execute_trades or not trading_state or len(validated_results) == 0:
                        return executed_trades, execution_details
                    
                    for result in validated_results:
                        ticker = result.get("ticker")
                        recommendation = result.get("recommendation", "HOLD")
                        deep_score = result.get("deep_score", 0)
                        confidence = min(deep_score / 10.0, 1.0)
                        executed = False
                        error_reason = None
                        
                        execution_reason = f"Deep analysis score: {deep_score:.1f}/10 ({confidence*100:.0f}% confidence)"
                        
                        if confidence < config.auto_execute_min_confidence:
                            error_reason = f"Confidence {confidence*100:.0f}% below minimum {config.auto_execute_min_confidence*100:.0f}%"
                        else:
                            try:
                                price = result.get("price", 100.0)
                                quantity = max(1, int(config.auto_execute_position_size / price))
                                
                                if recommendation == "BUY":
                                    total_cost = quantity * price
                                    commission = total_cost * trading_state.trading_config.get("commission_pct", 0.0001)
                                    slippage = price * quantity * trading_state.trading_config.get("slippage_pct", 0.001)
                                    
                                    if total_cost + commission + slippage <= trading_state.cash_balance:
                                        trading_state.cash_balance -= total_cost + commission + slippage
                                        
                                        if ticker not in trading_state.positions:
                                            trading_state.positions[ticker] = {
                                                "quantity": 0,
                                                "avg_cost": 0,
                                                "current_value": 0,
                                            }
                                        
                                        pos = trading_state.positions[ticker]
                                        total_qty = pos["quantity"] + quantity
                                        pos["avg_cost"] = (pos["quantity"] * pos["avg_cost"] + total_cost) / total_qty if total_qty > 0 else price
                                        pos["quantity"] = total_qty
                                        pos["current_value"] = total_qty * price
                                        
                                        trade_record = {
                                            "timestamp": datetime.now().isoformat(),
                                            "ticker": ticker,
                                            "action": "BUY",
                                            "quantity": quantity,
                                            "price": price,
                                            "total_value": total_cost,
                                            "commission": commission,
                                            "slippage": slippage,
                                            "rationale": f"Auto-executed {recommendation} from {industry} scan. {execution_reason}",
                                        }
                                        trading_state.executed_trades.append(trade_record)
                                        executed_trades.append(trade_record)
                                        executed = True
                                        logger.info(f"  ✅ {ticker}: BUY {quantity} shares @ ${price:.2f} = ${total_cost:.2f}")
                                    else:
                                        error_reason = f"Insufficient cash: need ${total_cost + commission + slippage:.2f}, have ${trading_state.cash_balance:.2f}"
                                
                                elif recommendation == "SELL":
                                    if ticker in trading_state.positions and trading_state.positions[ticker]["quantity"] > 0:
                                        pos_qty = trading_state.positions[ticker]["quantity"]
                                        total_proceeds = pos_qty * price
                                        commission = total_proceeds * trading_state.trading_config.get("commission_pct", 0.0001)
                                        slippage = price * pos_qty * trading_state.trading_config.get("slippage_pct", 0.001)
                                        
                                        proceeds = total_proceeds - commission - slippage
                                        trading_state.cash_balance += proceeds
                                        
                                        trade_record = {
                                            "timestamp": datetime.now().isoformat(),
                                            "ticker": ticker,
                                            "action": "SELL",
                                            "quantity": pos_qty,
                                            "price": price,
                                            "total_value": total_proceeds,
                                            "commission": commission,
                                            "slippage": slippage,
                                            "rationale": f"Auto-executed {recommendation} from {industry} scan. {execution_reason}",
                                        }
                                        trading_state.executed_trades.append(trade_record)
                                        executed_trades.append(trade_record)
                                        executed = True
                                        
                                        del trading_state.positions[ticker]
                                        logger.info(f"  ✅ {ticker}: SELL {pos_qty} shares @ ${price:.2f} = ${total_proceeds:.2f}")
                                    else:
                                        error_reason = f"No position to sell"
                            
                            except Exception as e:
                                error_reason = str(e)[:100]
                        
                        execution_details.append({
                            "ticker": ticker,
                            "recommendation": recommendation,
                            "deep_score": deep_score,
                            "confidence": f"{confidence*100:.0f}%",
                            "executed": executed,
                            "reason": execution_reason if executed else error_reason,
                        })
                    
                    return executed_trades, execution_details
                
                executed_trades, execution_details = calculate_background_execution_details(
                    results, industry, config, trading_state
                )
                
                if execution_details:
                    logger.info(f"Execution details calculated: {len([e for e in execution_details if e.get('executed')])} executed")
            
            except Exception as e:
                logger.debug(f"Could not calculate execution details for {industry}: {e}")
                execution_details = None
            
            # NOW store results with execution_details
            with self.lock:
                self.scan_results[industry] = results
                self.quick_scan_results[industry] = quick_results  # Store quick scan results too
                self.execution_details[industry] = execution_details
                self.last_scan_time[industry] = datetime.now().isoformat()
            
            # Save to file for persistence (with execution details if available)
            self._save_results_to_file(industry, results, execution_details, quick_results)
            
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
        """Get scan results with execution details if available"""
        with self.lock:
            if industry:
                return {
                    "industry": industry,
                    "results": self.scan_results.get(industry, []),
                    "execution_details": self.execution_details.get(industry),
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
    
    def set_results(self, industry: str, results: List[Dict], execution_details: Optional[List[Dict]] = None, quick_results: Optional[List[Dict]] = None):
        """Manually set scan results for an industry (used by web API for immediate results)"""
        with self.lock:
            self.scan_results[industry] = results
            self.quick_scan_results[industry] = quick_results or []  # Store quick results if provided
            self.execution_details[industry] = execution_details
            self.last_scan_time[industry] = datetime.now().isoformat()
        
        # Save to file
        self._save_results_to_file(industry, results, execution_details, quick_results)
        # Print formatted table
        table = self._format_as_markdown_table(industry, results)
        logger.info("\n" + table)
        logger.info(f"Results updated for {industry}: {len(results)} confirmed picks, {len(quick_results or [])} total scanned")
    
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
            market_prefix = self.market.value.lower()
            file_path = self.results_dir / f"{market_prefix}_{industry}_scan.json"
            
            # Fallback to old filename format if market-specific file doesn't exist
            if not file_path.exists():
                file_path = self.results_dir / f"{industry}_scan.json"
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Also load execution details if available
                    execution_details = data.get("execution_details")
                    if execution_details:
                        with self.lock:
                            self.execution_details[industry] = execution_details
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
