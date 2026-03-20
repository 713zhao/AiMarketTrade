"""
Real-time stock data fetcher using Yahoo Finance
"""

import yfinance as yf
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from src.market_config import Market, MARKET_INDUSTRY_TICKERS, MARKET_DEFAULT_TICKERS

logger = logging.getLogger(__name__)

# Mapping of industries to common tickers (default US market for backward compatibility)
INDUSTRY_TICKERS = {
    "AI": ["NVDA", "PLTR", "AI", "UPST", "NFLX", "GOOGL", "MSFT", "META"],
    "POWER": ["NEE", "DUK", "SO", "AEP", "EXC", "XEL", "ED"],
    "TECH": ["AAPL", "MSFT", "GOOGL", "TSLA", "META", "NVDA", "AMD", "INTEL"],
    "HEALTHCARE": ["JNJ", "PFE", "UNH", "LLY", "AZN", "ABBV"],
    "FINANCE": ["JPM", "BAC", "WFC", "GS", "MS", "BLK"],
    "ENERGY": ["XOM", "CVX", "COP", "MPC", "PSX"],
    "RETAIL": ["AMZN", "WMT", "TGT", "COST", "HD"],
    "TELECOM": ["VZ", "T", "TMUS", "S"],
}


class DataFetcher:
    """Fetch real-time stock data from Yahoo Finance"""
    
    @staticmethod
    def get_current_price(ticker: str) -> Optional[Dict]:
        """Get current price and basic info for a stock"""
        try:
            data = yf.Ticker(ticker)
            hist = data.history(period="1d")
            
            if hist.empty:
                logger.warning(f"No data found for {ticker}")
                return None
            
            current = hist.iloc[-1]
            info = data.info
            
            price = float(current["Close"])
            volume = int(current.get("Volume", 0))
            
            # Get company name
            company_name = info.get("longName", ticker)
            
            logger.info(f"✓ {ticker}: {company_name} - Price=${price:.2f}, Volume={volume:,}, Market Cap=${info.get('marketCap', 'N/A')}")
            
            return {
                "ticker": ticker,
                "company_name": company_name,  # NEW: Add company name
                "price": price,
                "volume": volume,
                "timestamp": datetime.now().isoformat(),
                "market_cap": info.get("marketCap", None),
                "pe_ratio": info.get("trailingPE", None),
            }
        except Exception as e:
            logger.error(f"✗ Error fetching data for {ticker}: {e}")
            return None
    
    @staticmethod
    def get_historical_data(ticker: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """Get historical price data"""
        try:
            data = yf.download(ticker, period=period, progress=False)
            if data.empty:
                logger.warning(f"No historical data for {ticker}")
                return None
            return data
        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {e}")
            return None
    
    @staticmethod
    def calculate_momentum(ticker: str, period: int = 14) -> Optional[Tuple[float, str]]:
        """Calculate price momentum using RSI"""
        try:
            data = yf.download(ticker, period="3mo", progress=False)
            
            if len(data) < period:
                logger.warning(f"Insufficient data for {ticker}: only {len(data)} days")
                return None
            
            # Handle both single and multi-index column structures
            close_col = ("Close", ticker) if ("Close", ticker) in data.columns else "Close"
            close_data = data[close_col]
            
            # Calculate RSI
            delta = close_data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Extract the last valid RSI value
            last_rsi_val = rsi.dropna().iloc[-1] if len(rsi.dropna()) > 0 else None
            if last_rsi_val is None:
                return None
            
            # Handle Series to scalar conversion
            if isinstance(last_rsi_val, pd.Series):
                current_rsi = float(last_rsi_val.iloc[0]) if len(last_rsi_val) > 0 else float(last_rsi_val)
            else:
                current_rsi = float(last_rsi_val)
            
            # Determine signal
            if current_rsi > 70:
                signal = "OVERBOUGHT"
            elif current_rsi < 30:
                signal = "OVERSOLD"
            else:
                signal = "NEUTRAL"
            
            logger.info(f"  📊 {ticker} RSI: {current_rsi:.2f} ({signal})")
            
            return current_rsi, signal
        except Exception as e:
            logger.error(f"✗ Error calculating momentum for {ticker}: {e}")
            return None
    
    @staticmethod
    def detect_volume_spike(ticker: str, days: int = 20) -> Optional[Tuple[float, bool]]:
        """Detect unusual volume spike"""
        try:
            data = yf.download(ticker, period="3mo", progress=False)
            
            if len(data) < days:
                return None
            
            # Handle both single and multi-index column structures
            volume_col = ("Volume", ticker) if ("Volume", ticker) in data.columns else "Volume"
            volume_data = data[volume_col]
            
            recent_volume_val = volume_data.iloc[-1]
            avg_volume_val = volume_data.iloc[-days:-1].mean()
            
            # Handle Series to scalar conversion
            if isinstance(recent_volume_val, pd.Series):
                recent_volume = float(recent_volume_val.iloc[0]) if len(recent_volume_val) > 0 else float(recent_volume_val)
            else:
                recent_volume = float(recent_volume_val) if recent_volume_val else 0
            
            if isinstance(avg_volume_val, pd.Series):
                avg_volume = float(avg_volume_val.iloc[0]) if len(avg_volume_val) > 0 else float(avg_volume_val)
            else:
                avg_volume = float(avg_volume_val) if avg_volume_val else 1
            
            spike_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            has_spike = spike_ratio > 1.5
            
            if has_spike:
                logger.info(f"  📈 {ticker} Volume Spike: {spike_ratio:.2f}x (Recent: {recent_volume:,.0f}, Avg: {avg_volume:,.0f})")
            
            return spike_ratio, has_spike
        except Exception as e:
            logger.error(f"✗ Error detecting volume spike for {ticker}: {e}")
            return None
    
    @staticmethod
    def calculate_macd(ticker: str) -> Optional[Dict]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            data = yf.download(ticker, period="3mo", progress=False)
            
            if len(data) < 26:
                return None
            
            # Handle both single and multi-index column structures
            close_col = ("Close", ticker) if ("Close", ticker) in data.columns else "Close"
            close_data = data[close_col]
            
            exp1 = close_data.ewm(span=12).mean()
            exp2 = close_data.ewm(span=26).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9).mean()
            histogram = macd - signal
            
            # Extract scalar values safely
            macd_last = macd.iloc[-1]
            signal_last = signal.iloc[-1]
            histogram_last = histogram.iloc[-1]
            histogram_prev = histogram.iloc[-2]
            
            # Handle Series to scalar conversion
            if isinstance(macd_last, pd.Series):
                macd_val = float(macd_last.iloc[0]) if len(macd_last) > 0 else 0
                signal_val = float(signal_last.iloc[0]) if len(signal_last) > 0 else 0
                histogram_val = float(histogram_last.iloc[0]) if len(histogram_last) > 0 else 0
                histogram_prev_val = float(histogram_prev.iloc[0]) if len(histogram_prev) > 0 else 0
            else:
                macd_val = float(macd_last)
                signal_val = float(signal_last)
                histogram_val = float(histogram_last)
                histogram_prev_val = float(histogram_prev)
            
            return {
                "macd": macd_val,
                "signal": signal_val,
                "histogram": histogram_val,
                "buy_signal": histogram_val > 0 and histogram_prev_val <= 0,
                "sell_signal": histogram_val < 0 and histogram_prev_val >= 0,
            }
        except Exception as e:
            logger.error(f"Error calculating MACD for {ticker}: {e}")
            return None
    
    @staticmethod
    def get_tickers_by_industry(industry: str, market: Market = Market.US) -> List[str]:
        """
        Get list of tickers for a specific industry
        
        Args:
            industry: Industry name (e.g., "AI", "Tech")
            market: Market to get tickers from (default: Market.US)
        
        Returns:
            List of tickers for the industry in the specified market
        """
        # Try to get from market config first
        try:
            return MARKET_INDUSTRY_TICKERS.get(market, {}).get(industry.upper(), [])
        except:
            # Fall back to INDUSTRY_TICKERS for backward compatibility
            return INDUSTRY_TICKERS.get(industry.upper(), [])
    
    @staticmethod
    def quick_scan_industry(industry: str, min_score: float = 3.0, max_candidates: int = 20, market: Market = Market.US) -> List[Dict]:
        """
        STAGE 1: Quick technical screening - returns only candidates with strong signals
        
        This is the filtering stage that eliminates ~70% of stocks
        Only candidates with score >= min_score are returned for deeper analysis
        
        Args:
            industry: Industry name (e.g., "AI", "Tech")
            min_score: Minimum quick score to pass through (default 3.0 out of 5)
            max_candidates: Maximum candidates to return (default 20)
            market: Market to scan (default: Market.US)
        
        Returns:
            List of candidates passing the quick filter
        """
        tickers = DataFetcher.get_tickers_by_industry(industry, market)
        candidates = []
        all_stocks = []  # Track all stocks for summary table
        
        logger.info(f"\n{'='*80}")
        logger.info(f"⚡ QUICK SCAN - FILTER STAGE: {industry.upper()} ({len(tickers)} stocks)")
        logger.info(f"{'='*80}")
        
        for ticker in tickers:
            try:
                # Get basic technical data
                price_data = DataFetcher.get_current_price(ticker)
                if not price_data:
                    continue
                
                momentum = DataFetcher.calculate_momentum(ticker)
                volume_spike = DataFetcher.detect_volume_spike(ticker)
                macd = DataFetcher.calculate_macd(ticker)
                
                # Calculate quick score
                buy_score = 0
                sell_score = 0
                reasons = []
                rsi_value = None
                rsi_status = "NEUTRAL"
                
                if momentum:
                    rsi_value, rsi_signal = momentum
                    if rsi_signal == "OVERSOLD":
                        buy_score += 2
                        rsi_status = "OVERSOLD"
                        reasons.append(f"RSI{rsi_value:.0f}↓")
                    elif rsi_signal == "OVERBOUGHT":
                        sell_score += 2
                        rsi_status = "OVERBOUGHT"
                        reasons.append(f"RSI{rsi_value:.0f}↑")
                    else:
                        rsi_status = "NEUTRAL"
                
                if volume_spike:
                    vol_ratio, has_spike = volume_spike
                    if has_spike:
                        buy_score += 1
                        reasons.append(f"Vol{vol_ratio:.1f}x")
                
                if macd:
                    if macd.get("buy_signal"):
                        buy_score += 2
                        reasons.append("MACD↑")
                    elif macd.get("sell_signal"):
                        sell_score += 2
                        reasons.append("MACD↓")
                
                quick_score = max(buy_score, sell_score)
                signal = "BUY" if buy_score > sell_score else "SELL" if sell_score > buy_score else "HOLD"
                
                # Track all stocks for summary
                stock_info = {
                    "ticker": ticker,
                    "price": price_data.get("price"),
                    "quick_signal": signal,
                    "quick_score": quick_score,
                    "buy_score": buy_score,
                    "sell_score": sell_score,
                    "reasons": reasons,
                    "rsi": rsi_value,
                    "rsi_status": rsi_status,
                    "volume_spike": volume_spike[0] if volume_spike else None,
                    "passed": quick_score >= min_score,
                }
                all_stocks.append(stock_info)
                
                # FILTER: Only keep strong signals
                if quick_score >= min_score:
                    candidates.append(stock_info)
                    logger.info(f"  ✓ {ticker:6s} PASS: {signal:4s} (score {quick_score}/5) {' | '.join(reasons)}")
                else:
                    logger.debug(f"  ✗ {ticker:6s} skip: score {quick_score}/5 < {min_score} (not interesting)")
                
            except Exception as e:
                logger.debug(f"  ✗ {ticker}: {str(e)[:50]}")
                continue
        
        # Sort by score and limit to max_candidates
        candidates = sorted(candidates, key=lambda x: x["quick_score"], reverse=True)[:max_candidates]
        
        logger.info(f"\n✓ Quick scan complete: {len(candidates)} candidates passed filter")
        logger.info(f"  (out of {len(tickers)} stocks analyzed)")
        
        # Print summary table
        logger.info(f"\n### {industry.upper()} Industry Scan Results\n")
        logger.info("| Ticker | Price | RSI | Status | Signal | Reason |")
        logger.info("|--------|-------|-----|--------|--------|--------|")
        
        # Sort all_stocks by RSI extremity (OVERSOLD first, then OVERBOUGHT, then NEUTRAL)
        def sort_key(stock):
            status_order = {"OVERSOLD": 0, "OVERBOUGHT": 1, "NEUTRAL": 2}
            return (status_order.get(stock["rsi_status"], 2), -stock["quick_score"])
        
        all_stocks_sorted = sorted(all_stocks, key=sort_key)
        
        for stock in all_stocks_sorted:
            price_str = f"${stock['price']:.2f}" if stock['price'] else "N/A"
            rsi_str = f"{stock['rsi']:.2f}" if stock['rsi'] is not None else "N/A"
            reason_str = " | ".join(stock['reasons']) if stock['reasons'] else "No signals"
            
            logger.info(f"| **{stock['ticker']}** | {price_str} | {rsi_str} | {stock['rsi_status']} | {stock['quick_signal']} | {reason_str} |")
        
        logger.info(f"\n{'='*80}\n")
        
        # Flush to ensure output appears immediately
        import sys
        sys.stdout.flush()
        
        # Return both candidates and all_stocks for dashboard display
        return {
            "candidates": candidates,
            "all_stocks": all_stocks
        }
    
    @staticmethod
    def scan_industry(industry: str, market: Market = Market.US) -> List[Dict]:
        """
        Scan all tickers in an industry for trading signals
        
        Args:
            industry: Industry name (e.g., "AI", "Tech")
            market: Market to scan (default: Market.US)
        
        Returns:
            List of trading signals sorted by buy score
        """
        tickers = DataFetcher.get_tickers_by_industry(industry, market)
        results = []
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 SCANNING {industry.upper()} INDUSTRY ({market.value} MARKET) - {len(tickers)} stocks")
        logger.info(f"{'='*80}")
        
        for ticker in tickers:
            try:
                signals = {
                    "ticker": ticker,
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Price and volume
                price_data = DataFetcher.get_current_price(ticker)
                if price_data:
                    signals.update(price_data)
                else:
                    logger.warning(f"✗ {ticker}: No price data")
                    continue
                
                # Momentum (RSI)
                momentum = DataFetcher.calculate_momentum(ticker)
                if momentum:
                    signals["rsi"], signals["rsi_signal"] = momentum
                else:
                    logger.debug(f"    ⚠ {ticker}: No momentum data")
                
                # Volume spike
                volume_spike = DataFetcher.detect_volume_spike(ticker)
                if volume_spike:
                    signals["volume_spike_ratio"], signals["has_volume_spike"] = volume_spike
                else:
                    logger.debug(f"    ⚠ {ticker}: No volume spike data")
                
                # MACD
                macd = DataFetcher.calculate_macd(ticker)
                if macd:
                    signals.update(macd)
                else:
                    logger.debug(f"    ⚠ {ticker}: No MACD data")
                
                # Log signal values for debugging
                logger.debug(f"    📊 {ticker} signals: rsi_signal={signals.get('rsi_signal')}, has_volume_spike={signals.get('has_volume_spike')}, buy_signal={signals.get('buy_signal')}, sell_signal={signals.get('sell_signal')}")
                
                # Generate trading signal with debug output
                buy_score = 0
                sell_score = 0
                reasons = []
                
                if signals.get("rsi_signal") == "OVERSOLD":
                    buy_score += 2
                    reasons.append("RSI Oversold(+2)")
                elif signals.get("rsi_signal") == "OVERBOUGHT":
                    sell_score += 2
                    reasons.append("RSI Overbought(+2)")
                
                if signals.get("has_volume_spike"):
                    buy_score += 1
                    reasons.append("Volume Spike(+1)")
                
                if signals.get("buy_signal"):
                    buy_score += 2
                    reasons.append("MACD Buy(+2)")
                elif signals.get("sell_signal"):
                    sell_score += 2
                    reasons.append("MACD Sell(+2)")
                
                signals["buy_score"] = buy_score
                signals["sell_score"] = sell_score
                signals["recommendation"] = "BUY" if buy_score > sell_score else "SELL" if sell_score > buy_score else "HOLD"
                
                # Store reasons in signal
                reason_str = " | ".join(reasons) if reasons else "No signals"
                signals["reason"] = reason_str
                signals["reasons"] = reasons  # Also store as list for detailed view
                
                # Log the decision
                logger.info(f"  → {ticker}: {signals['recommendation']:4s} (Buy:{buy_score} Sell:{sell_score}) {reason_str}")
                
                results.append(signals)
            
            except Exception as e:
                logger.error(f"✗ Error scanning {ticker}: {e}")
                continue
        
        logger.info(f"\n✓ Scan complete: {len(results)} stocks analyzed in {industry}")
        logger.info(f"{'='*80}\n")
        
        return sorted(results, key=lambda x: x["buy_score"], reverse=True)


if __name__ == "__main__":
    # Test the fetcher
    fetcher = DataFetcher()
    
    # Test single stock
    print("=== Current Price ===")
    price = fetcher.get_current_price("AAPL")
    print(price)
    
    # Test momentum
    print("\n=== Momentum ===")
    momentum = fetcher.calculate_momentum("AAPL")
    print(f"RSI: {momentum[0]:.2f}, Signal: {momentum[1]}")
    
    # Test industry scan
    print("\n=== Tech Industry Scan ===")
    results = fetcher.scan_industry("Tech")
    for r in results[:5]:
        print(f"{r['ticker']}: {r['recommendation']} (Buy: {r['buy_score']}, Sell: {r['sell_score']})")
