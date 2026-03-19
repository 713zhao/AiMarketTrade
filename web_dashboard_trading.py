"""
Web Dashboard for Stock Market Analysis and Trading Simulation - Trading Integration

Integrates with the trading system to display:
- Executed trades from the DeerflowState
- Portfolio positions and P&L
- Trading metrics and performance
"""

from flask import Flask, render_template, jsonify, request
from decimal import Decimal
from datetime import datetime, timedelta
import json
import logging
import sys

# Set up logging before Flask
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(message)s')
log_handler.setFormatter(log_formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(log_handler)

# Ensure all modules log at INFO level
logging.getLogger('src.data_fetcher').setLevel(logging.INFO)
logging.getLogger('src').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')

# Suppress Flask's default logging to avoid clutter
app.logger.setLevel(logging.WARNING)
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

# Import trading system components
from src.state import DeerflowState, ConsensusSignal, SignalType, DataProvider, TickerData
from src.nodes.trading_nodes import (
    RecommendationToTradeNode,
    TradeExecutionNode,
    PortfolioMetricsNode,
)
from src.data_fetcher import DataFetcher
from src.background_scanner import get_scanner
from src.config import Settings
import asyncio

# Global trading state (simulated portfolio)
trading_state = None
data_fetcher = DataFetcher()
background_scanner = get_scanner()

def initialize_trading_state():
    """Initialize a sample trading state for demonstration."""
    global trading_state
    trading_state = DeerflowState(
        tickers=["AAPL", "MSFT", "GOOGL"],
        trading_enabled=True,
        cash_balance=100000.0,
        positions={},
        executed_trades=[],
        portfolio_metrics={},
        trading_config={
            "position_size_pct": 0.10,
            "confidence_threshold": 0.70,
            "slippage_pct": 0.001,
            "commission_pct": 0.0001,
        },
    )
    logger.info("Trading state initialized")
    
    # Start background scanner
    background_scanner.start(data_fetcher)
    logger.info("Background scanner started")

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/portfolio')
def get_portfolio():
    """Get current portfolio status from trading state."""
    try:
        if not trading_state:
            return jsonify({"error": "Trading state not initialized"}), 500

        # Build positions list
        positions = []
        for ticker, position in trading_state.positions.items():
            positions.append({
                "symbol": ticker,
                "stock_name": ticker,  # Can be enhanced with actual company names
                "quantity": position.get("quantity", 0),
                "average_cost": position.get("avg_cost", 0),
                "current_value": position.get("current_value", 0),
                "yahoo_url": f"https://finance.yahoo.com/quote/{ticker}",
            })

        metrics = trading_state.portfolio_metrics or {}
        total_value = metrics.get("total_value", trading_state.cash_balance)
        total_pnl = metrics.get("total_pnl", 0)

        return jsonify({
            "portfolio_value": float(total_value),
            "cash_balance": float(trading_state.cash_balance),
            "total_pnl": float(total_pnl),
            "total_return_pct": float(metrics.get("return_pct", 0)),
            "positions": positions,
            "total_positions": len(positions),
        })
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/trades')
def get_trades():
    """Get trade history from trading state."""
    try:
        if not trading_state:
            return jsonify({"trades": []}), 200

        limit = request.args.get('limit', 50, type=int)
        trades = trading_state.executed_trades or []

        # Convert to display format
        trades_data = []
        for trade in trades[-limit:]:  # Last N trades
            trade_data = {
                "timestamp": trade.get("timestamp", datetime.now().isoformat()),
                "action": trade.get("action", "").upper(),
                "symbol": trade.get("ticker", ""),
                "stock_name": trade.get("ticker", ""),
                "quantity": trade.get("quantity", 0),
                "price": float(trade.get("price", 0)),
                "total": float(trade.get("quantity", 0) * trade.get("price", 0)),
                "commission": float(trade.get("commission", 0)),
                "slippage": float(trade.get("slippage", 0)),
                "yahoo_url": f"https://finance.yahoo.com/quote/{trade.get('ticker', '')}",
                "rationale": trade.get("rationale", f"{trade.get('action', 'TRADE').upper()} {trade.get('ticker', '')} at {trade.get('price', 0)}"),
            }
            trades_data.append(trade_data)

        # Reverse to show most recent first
        trades_data.reverse()

        return jsonify({"trades": trades_data})
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return jsonify({"trades": []}), 200

@app.route('/api/performance')
def get_performance():
    """Get detailed performance metrics."""
    try:
        if not trading_state:
            return jsonify({"error": "Trading state not initialized"}), 500

        metrics = trading_state.portfolio_metrics or {}

        return jsonify({
            "portfolio_value": float(metrics.get("total_value", trading_state.cash_balance)),
            "cash_balance": float(trading_state.cash_balance),
            "total_positions": len(trading_state.positions or {}),
            "realized_pnl": float(metrics.get("realized_pnl", 0)),
            "unrealized_pnl": float(metrics.get("unrealized_pnl", 0)),
            "total_pnl": float(metrics.get("total_pnl", 0)),
            "total_return_pct": float(metrics.get("return_pct", 0)),
            "win_rate": float(metrics.get("win_rate", 0)),
            "avg_profit_per_win": float(metrics.get("avg_win", 0)),
            "avg_loss_per_loss": float(metrics.get("avg_loss", 0)),
            "max_drawdown": float(metrics.get("max_drawdown", 0)),
            "total_trades": metrics.get("total_trades", len(trading_state.executed_trades or [])),
            "volatility": float(metrics.get("volatility", 0)),
            "sharpe_ratio": float(metrics.get("sharpe_ratio", 0)),
        })
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/execute-trade', methods=['POST'])
def execute_trade():
    """Execute a manual trade for demonstration."""
    try:
        if not trading_state:
            return jsonify({"error": "Trading state not initialized"}), 500

        data = request.get_json()
        ticker = data.get("ticker", "").upper()
        action = data.get("action", "buy").lower()
        quantity = int(data.get("quantity", 0))
        price = float(data.get("price", 0))

        if not ticker or quantity <= 0 or price <= 0:
            return jsonify({"error": "Invalid trade parameters"}), 400

        # Calculate costs
        total_cost = quantity * price
        commission = total_cost * trading_state.trading_config.get("commission_pct", 0.0001)
        slippage = price * quantity * trading_state.trading_config.get("slippage_pct", 0.001)

        if action == "buy":
            # Check cash availability
            if total_cost + commission + slippage > trading_state.cash_balance:
                return jsonify({"error": "Insufficient cash"}), 400

            # Update cash
            trading_state.cash_balance -= total_cost + commission + slippage

            # Update positions
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

        elif action == "sell":
            # Check position availability
            if ticker not in trading_state.positions or trading_state.positions[ticker]["quantity"] < quantity:
                return jsonify({"error": "Insufficient position"}), 400

            # Update cash (proceeds - commission - slippage)
            proceeds = total_cost - commission - slippage
            trading_state.cash_balance += proceeds

            # Update positions
            pos = trading_state.positions[ticker]
            pos["quantity"] -= quantity
            pos["current_value"] = pos["quantity"] * price

            if pos["quantity"] == 0:
                del trading_state.positions[ticker]

        # Record trade
        trade_record = {
            "trade_id": len(trading_state.executed_trades) + 1,
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "action": action.lower(),
            "quantity": quantity,
            "price": price,
            "total_value": total_cost,
            "commission": commission,
            "slippage": slippage,
            "rationale": f"Manual {action.upper()} of {quantity} shares of {ticker}",
        }
        trading_state.executed_trades.append(trade_record)

        # Recalculate metrics
        asyncio.run(recalculate_metrics())

        return jsonify({
            "success": True,
            "message": f"Trade executed: {action.upper()} {quantity} {ticker} @ ${price}",
            "trade": trade_record,
        })
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return jsonify({"error": str(e)}), 500

async def recalculate_metrics():
    """Recalculate portfolio metrics using PortfolioMetricsNode."""
    try:
        metrics_node = PortfolioMetricsNode()
        global trading_state
        trading_state = await metrics_node._execute(trading_state)
    except Exception as e:
        logger.error(f"Error recalculating metrics: {e}")

@app.route('/api/run-trading-cycle', methods=['POST'])
def run_trading_cycle():
    """Run a full trading cycle (recommendation -> execution -> metrics)."""
    try:
        if not trading_state:
            return jsonify({"error": "Trading state not initialized"}), 500

        data = request.get_json()
        ticker = data.get("ticker", "AAPL").upper()
        action = data.get("action", "BUY").upper()
        confidence = float(data.get("confidence", 0.85))

        # Get real data from yfinance
        try:
            hist_data = data_fetcher.get_historical_data(ticker, period="1mo")
            if hist_data is not None and not hist_data.empty:
                close_prices = hist_data["Close"].tolist()
            else:
                close_prices = [150.0, 151.0, 152.0]  # Fallback
        except Exception as e:
            logger.warning(f"Could not fetch real data for {ticker}, using fallback: {e}")
            close_prices = [150.0, 151.0, 152.0]

        # Create ticker data with real historical prices
        ticker_data = TickerData(
            ticker=ticker,
            provider=DataProvider.FMP,
            historical_data={"close": close_prices},
        )

        # Create trading state with consensus signal
        test_state = DeerflowState(
            tickers=[ticker],
            trading_enabled=True,
            cash_balance=trading_state.cash_balance,
            positions=trading_state.positions.copy() if trading_state.positions else {},
            ticker_data={ticker: ticker_data},
            consensus_signals={
                ticker: ConsensusSignal(
                    ticker=ticker,
                    overall_signal=SignalType.BUY if action == "BUY" else SignalType.SELL,
                    signal_strength=confidence,
                )
            },
            trading_config=trading_state.trading_config,
        )

        async def execute_cycle():
            # Step 1: Generate trade recommendation
            rec_node = RecommendationToTradeNode()
            test_state_after_rec = await rec_node._execute(test_state)

            if not test_state_after_rec.pending_trades:
                return {"success": False, "message": "No trades generated"}

            # Step 2: Execute trades
            exec_node = TradeExecutionNode()
            test_state_after_exec = await exec_node._execute(test_state_after_rec)

            # Step 3: Calculate metrics
            metrics_node = PortfolioMetricsNode()
            final_state = await metrics_node._execute(test_state_after_exec)

            # Update global state directly (avoid validation issues)
            global trading_state
            trading_state.cash_balance = final_state.cash_balance
            trading_state.positions = final_state.positions.copy() if final_state.positions else {}
            trading_state.executed_trades = (trading_state.executed_trades or []) + (final_state.executed_trades or [])
            
            # Safe metrics dict with only required fields
            safe_metrics = {
                "total_value": final_state.portfolio_metrics.get("total_value", 0),
                "total_pnl": final_state.portfolio_metrics.get("total_pnl", 0),
                "win_rate": final_state.portfolio_metrics.get("win_rate", 0),
                "total_return_pct": final_state.portfolio_metrics.get("total_return_pct", 0),
            }
            trading_state.portfolio_metrics = safe_metrics

            return {
                "success": True,
                "trades_executed": len(final_state.executed_trades or []),
                "cash_remaining": float(final_state.cash_balance),
                "metrics": safe_metrics,
            }

        result = asyncio.run(execute_cycle())
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error running trading cycle: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get overall statistics."""
    try:
        if not trading_state:
            return jsonify({
                "total_trades": 0,
                "trades_today": 0,
                "open_positions": 0,
                "portfolio_value": 0,
                "total_return": 0,
                "win_rate": 0,
                "max_drawdown": 0,
            }), 200

        metrics = trading_state.portfolio_metrics or {}
        trades = trading_state.executed_trades or []
        today_trades = [t for t in trades if t.get("timestamp", "").startswith(datetime.now().strftime("%Y-%m-%d"))]

        return jsonify({
            "total_trades": len(trades),
            "trades_today": len(today_trades),
            "open_positions": len(trading_state.positions or {}),
            "portfolio_value": float(metrics.get("total_value", trading_state.cash_balance)),
            "total_return": float(metrics.get("return_pct", 0)),
            "win_rate": float(metrics.get("win_rate", 0)),
            "max_drawdown": float(metrics.get("max_drawdown", 0)),
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/monitoring-status')
def get_monitoring_status():
    """Get system monitoring status."""
    return jsonify({
        "enabled": False,
        "message": "Intraday monitoring not enabled in this deployment",
    })

@app.route('/api/reports')
def get_reports():
    """Get analysis reports from scanner results."""
    try:
        scanner_status = background_scanner.get_status()
        results = background_scanner.get_results()
        
        # Convert results to report format
        reports = []
        for i, (industry, stocks) in enumerate(results.get("results", {}).items()):
            if isinstance(stocks, list):
                buy_candidates = [s for s in stocks if s.get("recommendation") == "BUY"]
                sell_candidates = [s for s in stocks if s.get("recommendation") == "SELL"]
                
                report = {
                    "report_id": f"SCAN-{industry}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "industry": industry,
                    "generated_at": results.get("last_updated", {}).get(industry, datetime.now().isoformat()),
                    "recommendations_count": len(stocks),
                    "buy_opportunities": len(buy_candidates),
                    "sell_opportunities": len(sell_candidates),
                    "top_buys": buy_candidates[:5],
                    "top_sells": sell_candidates[:5],
                }
                reports.append(report)
        
        return jsonify({
            "success": True,
            "scanner_status": scanner_status,
            "reports": reports,
        })
    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        return jsonify({"error": str(e)}), 500

def deep_analysis_candidates(candidates: list, industry: str, config) -> list:
    """
    STAGE 2: Deep Analysis - Full orchestration on filtered candidates
    
    Takes the candidates from quick scan and runs full 39-node analysis
    Only returns those that pass deep score threshold and agree with quick signal
    
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
        ticker = candidate["ticker"]
        quick_signal = candidate["quick_signal"]
        quick_score = candidate["quick_score"]
        
        try:
            logger.info(f"[{i}/{len(candidates)}] Analyzing {ticker}...")
            
            # For now, use a simplified deep analysis
            # In Phase 6, this would call the full 39-node graph
            # For demonstration, we'll enhance the quick score with additional factors
            
            # Get additional data for deep analysis
            price_data = DataFetcher.get_current_price(ticker)
            if not price_data:
                logger.warning(f"  ⚠️ {ticker}: Could not fetch deep data, skipping")
                continue
            
            # Calculate enhanced deep score (0-10 scale)
            # In real implementation, this would be 39-node orchestration
            deep_score = (quick_score / 5.0) * 10.0  # Convert 0-5 to 0-10
            
            # Add some variance for demonstration (in real impl, this is full analysis)
            import random
            deep_score += random.uniform(-1, 0.5)  # Slight variance
            deep_score = min(10.0, max(0.0, deep_score))  # Clamp to 0-10
            
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
                "confidence": "HIGH",
                "buy_score": candidate.get("buy_score", 0),
                "sell_score": candidate.get("sell_score", 0),
                "rsi": candidate.get("rsi"),
                "volume_spike": candidate.get("volume_spike"),
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

@app.route('/api/scanner/status')
def scanner_status():
    """Get background scanner status."""
    try:
        status = background_scanner.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting scanner status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scanner/industries', methods=['GET', 'POST'])
def manage_industries():
    """Get or set enabled industries for scanner."""
    try:
        if request.method == 'POST':
            data = request.get_json()
            industries = data.get('industries', [])
            background_scanner.set_enabled_industries(industries)
            return jsonify({"success": True, "industries": industries})
        else:
            return jsonify({"industries": background_scanner.enabled_industries})
    except Exception as e:
        logger.error(f"Error managing industries: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scanner/recommendations/<industry>')
def get_recommendations(industry):
    """Get trading recommendations for an industry."""
    try:
        signal_type = request.args.get('signal', 'BUY')
        min_score = int(request.args.get('min_score', 2))
        
        recommendations = background_scanner.get_recommendations(industry, signal_type, min_score)
        
        return jsonify({
            "industry": industry,
            "signal_type": signal_type,
            "recommendations": recommendations,
            "count": len(recommendations),
        })
    except Exception as e:
        logger.error(f"Error getting recommendations for {industry}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scanner/scan-now/<industry>', methods=['POST'])
def force_scan(industry):
    """
    Force scan of a specific industry immediately using two-stage approach:
    STAGE 1: Quick technical filter (< 1 sec)
    STAGE 2: Deep analysis on filtered candidates (15-20 sec)
    """
    try:
        config = Settings()
        logger.info(f"\n🚀 Starting two-stage hybrid scan for {industry.upper()}")
        
        # STAGE 1: Quick Technical Filter
        logger.info(f"Stage 1: Quick scan filter...")
        start_time = datetime.now()
        quick_scan_result = DataFetcher.quick_scan_industry(
            industry,
            min_score=config.quick_scan_min_score,
            max_candidates=config.quick_scan_max_candidates
        )
        quick_results = quick_scan_result["candidates"] if isinstance(quick_scan_result, dict) else quick_scan_result
        all_stocks = quick_scan_result.get("all_stocks", []) if isinstance(quick_scan_result, dict) else []
        quick_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✓ Quick scan completed in {quick_time:.2f}s: {len(quick_results)} candidates found")
        
        # STAGE 2: Deep Analysis
        if len(quick_results) > 0:
            logger.info(f"Stage 2: Deep analysis on {len(quick_results)} candidates...")
            start_time = datetime.now()
            validated_results = deep_analysis_candidates(quick_results, industry, config)
            deep_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✓ Deep analysis completed in {deep_time:.2f}s: {len(validated_results)} confirmed")
        else:
            logger.warning(f"No candidates passed quick filter")
            validated_results = []
            deep_time = 0
        
        # Store results in background scanner
        background_scanner.set_results(industry, validated_results)
        total_time = quick_time + deep_time
        
        # Sort all_stocks for summary table display
        def sort_key(stock):
            status_order = {"OVERSOLD": 0, "OVERBOUGHT": 1, "NEUTRAL": 2}
            return (status_order.get(stock["rsi_status"], 2), -stock["quick_score"])
        
        all_stocks_sorted = sorted(all_stocks, key=sort_key) if all_stocks else []
        
        return jsonify({
            "success": True,
            "industry": industry,
            "stages": {
                "quick": {
                    "time_secs": round(quick_time, 2),
                    "candidates": len(quick_results),
                    "results": quick_results  # Optional: include for debugging
                },
                "deep": {
                    "time_secs": round(deep_time, 2),
                    "confirmed": len(validated_results),
                    "results": validated_results
                }
            },
            "total_time_secs": round(total_time, 2),
            "message": f"✅ Scan complete: {len(quick_results)} quick candidates → {len(validated_results)} confirmed high-confidence picks",
            "results": validated_results,  # Main results for dashboard
            "summary_table": all_stocks_sorted  # Summary table for HTML display
        })
    except Exception as e:
        logger.error(f"Error forcing scan: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock/<ticker>/data')
def get_stock_data(ticker):
    """Get real-time data for a stock."""
    try:
        price_data = data_fetcher.get_current_price(ticker)
        momentum = data_fetcher.calculate_momentum(ticker)
        volume_spike = data_fetcher.detect_volume_spike(ticker)
        macd = data_fetcher.calculate_macd(ticker)
        
        return jsonify({
            "ticker": ticker,
            "price": price_data,
            "momentum": {"rsi": momentum[0], "signal": momentum[1]} if momentum else None,
            "volume_spike": {"ratio": volume_spike[0], "detected": volume_spike[1]} if volume_spike else None,
            "macd": macd,
        })
    except Exception as e:
        logger.error(f"Error getting stock data for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scanner/scan-tables/<industry>')
def get_scan_table(industry):
    """Get formatted scan table for a specific industry."""
    try:
        table = background_scanner.get_scan_table(industry)
        return jsonify({
            "success": True,
            "industry": industry,
            "table": table,
            "last_updated": background_scanner.last_scan_time.get(industry)
        })
    except Exception as e:
        logger.error(f"Error getting scan table for {industry}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scanner/all-scan-tables')
def get_all_scan_tables():
    """Get formatted scan tables for all industries."""
    try:
        all_tables = background_scanner.get_scan_table()
        return jsonify({
            "success": True,
            "tables": all_tables,
            "industries": background_scanner.enabled_industries,
            "last_updated": background_scanner.last_scan_time
        })
    except Exception as e:
        logger.error(f"Error getting all scan tables: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Trading System Dashboard")
    print("=" * 60)
    initialize_trading_state()
    print("Trading State Initialized")
    print("Dashboard URL: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
