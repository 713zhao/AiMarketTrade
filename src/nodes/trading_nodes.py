"""
Trading nodes for virtual portfolio execution and tracking.

Implements async LangGraph nodes for the trading pipeline:
1. RecommendationToTradeNode: Convert analyst recommendations to trade instructions
2. TradeExecutionNode: Execute trades with position and cash validation
3. PortfolioMetricsNode: Calculate portfolio performance metrics
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional

from src.models import DeerflowState, TradeAction, ExecutedTrade, PortfolioMetrics


logger = logging.getLogger(__name__)


class RecommendationToTradeNode:
    """
    Convert analyst consensus recommendations into trade instructions.
    
    Applies position sizing rules and confidence thresholds to generate
    pending trades that will be executed by the TradeExecutionNode.
    """
    
    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """
        Convert consensus signals to pending trades.
        
        Args:
            state: Current DeerflowState with consensus_signals
            
        Returns:
            Updated state with pending_trades populated
        """
        if not state.trading_enabled:
            logger.debug("Trading disabled, skipping trade generation")
            return state
        
        if not state.consensus_signals:
            logger.debug("No consensus signals available")
            return state
        
        # Get trading configuration
        config = state.trading_config
        position_size_pct = config.get("position_size_pct", 0.1)  # 10% default
        confidence_threshold = config.get("confidence_threshold", 0.70)
        
        logger.info(f"Converting recommendations to trades (position_size={position_size_pct*100}%, confidence_min={confidence_threshold})")
        
        pending_trades = []
        
        # Process each consensus signal
        for ticker, signal in state.consensus_signals.items():
            logger.info(f"\n📊 Evaluating {ticker}:")
            logger.info(f"   Signal: {signal.overall_signal.value.upper()}")
            logger.info(f"   Confidence: {signal.signal_strength:.2f}")
            logger.info(f"   Threshold: {confidence_threshold:.2f}")
            
            # Check confidence threshold
            if signal.signal_strength < confidence_threshold:
                logger.warning(f"   ❌ REJECTED: Signal strength {signal.signal_strength:.2f} < threshold {confidence_threshold:.2f}")
                continue
            
            logger.info(f"   ✓ Confidence check passed")
            
            # Skip HOLD signals
            if signal.overall_signal.value == "hold":
                logger.info(f"   ❌ SKIPPED: HOLD signal (no trade action)")
                continue
            
            # Get current price from ticker data
            ticker_data = state.ticker_data.get(ticker)
            if not ticker_data or not ticker_data.historical_data:
                logger.warning(f"   ❌ FAILED: No price data available")
                continue
            
            prices = ticker_data.historical_data.get("close", [])
            if not prices or len(prices) == 0:
                logger.warning(f"   ❌ FAILED: No closing prices in historical data")
                continue
            
            current_price = float(prices[-1])
            logger.info(f"   Price: ${current_price:.2f}")
            
            # Calculate trade size
            cash_to_trade = state.cash_balance * position_size_pct
            quantity = int(cash_to_trade / current_price)
            
            logger.info(f"   Cash available: ${state.cash_balance:.2f}")
            logger.info(f"   Position size (10%): ${cash_to_trade:.2f}")
            logger.info(f"   Calculated qty: {quantity} shares")
            
            if quantity == 0:
                logger.warning(f"   ❌ FAILED: Calculated quantity is 0 (insufficient cash or price too high)")
                continue
            
            # Determine action
            action = "buy" if signal.overall_signal.value in ["buy", "strong_buy"] else "sell"
            
            trade = {
                "ticker": ticker,
                "action": action,
                "quantity": quantity,
                "price": current_price,
                "confidence": signal.signal_strength,
                "rationale": f"Consensus signal: {signal.overall_signal.value}",
                "created_at": datetime.utcnow().isoformat(),
            }
            
            pending_trades.append(trade)
            logger.info(f"   ✅ APPROVED: Generated {action.upper()} order for {quantity} shares @ ${current_price:.2f}\n")
        
        # Update state
        state.pending_trades = pending_trades
        
        if pending_trades:
            logger.info(f"Generated {len(pending_trades)} pending trades")
        else:
            logger.info("No pending trades generated (all signals filtered out)")
        
        return state


class TradeExecutionNode:
    """
    Execute pending trades with validation and portfolio updates.
    
    Validates cash availability, position sizes, and updates portfolio
    state with new positions and executed trade records.
    """
    
    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """
        Execute all pending trades.
        
        Args:
            state: Current state with pending_trades
            
        Returns:
            Updated state with executed_trades and positions
        """
        if not state.trading_enabled:
            return state
        
        if not state.pending_trades:
            logger.debug("No pending trades to execute")
            return state
        
        logger.info(f"Executing {len(state.pending_trades)} pending trades")
        
        executed_trades = []
        
        # Process each pending trade
        for trade_spec in state.pending_trades:
            try:
                executed_trade = await self._execute_single_trade(state, trade_spec)
                if executed_trade:
                    executed_trades.append(executed_trade)
                    state.executed_trades.append(executed_trade)
                    
            except Exception as e:
                logger.error(f"Error executing trade {trade_spec.get('ticker')}: {str(e)}")
                state.add_error("trade_executor", str(e), trade_spec.get('ticker'))
        
        # Clear pending trades
        state.pending_trades = []
        
        logger.info(f"Executed {len(executed_trades)} trades successfully")
        return state
    
    async def _execute_single_trade(
        self,
        state: DeerflowState,
        trade_spec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a single trade with validation.
        
        Args:
            state: Current portfolio state
            trade_spec: Trade specification with ticker, action, quantity, price
            
        Returns:
            Executed trade record or None if failed
        """
        ticker = trade_spec["ticker"]
        action = trade_spec["action"]
        quantity = trade_spec["quantity"]
        price = float(trade_spec["price"])
        
        # Apply slippage
        slippage_pct = float(state.trading_config.get("slippage_pct", 0.001))
        slippage_amount = price * quantity * slippage_pct
        
        # Apply commission
        commission_pct = float(state.trading_config.get("commission_pct", 0.0001))
        commission = price * quantity * commission_pct
        
        trade_value = price * quantity
        total_cost = trade_value + commission + slippage_amount if action == "buy" else trade_value - commission - slippage_amount
        
        # Validate trade
        if action == "buy":
            if state.cash_balance < trade_value:
                logger.warning(
                    f"{ticker}: Insufficient cash for BUY (need ${trade_value:.2f}, have ${state.cash_balance:.2f})"
                )
                return None
        else:  # sell
            position = state.positions.get(ticker, {})
            current_quantity = position.get("quantity", 0)
            if current_quantity < quantity:
                logger.warning(
                    f"{ticker}: Insufficient position for SELL (need {quantity}, have {current_quantity})"
                )
                return None
        
        # Execute trade
        trade_id = str(uuid.uuid4())
        
        if action == "buy":
            # Update or create position
            if ticker not in state.positions:
                state.positions[ticker] = {
                    "quantity": 0,
                    "avg_cost": 0.0,
                    "current_value": 0.0
                }
            
            pos = state.positions[ticker]
            
            # Calculate new average cost
            old_cost_basis = pos["avg_cost"] * pos["quantity"]
            new_total_cost = old_cost_basis + trade_value
            new_total_quantity = pos["quantity"] + quantity
            
            pos["avg_cost"] = new_total_cost / new_total_quantity if new_total_quantity > 0 else 0.0
            pos["quantity"] = new_total_quantity
            pos["current_value"] = price * new_total_quantity
            
            state.cash_balance -= (trade_value + commission + slippage_amount)
            
            logger.info(
                f"{ticker}: BUY {quantity} @ ${price:.2f} | "
                f"New position: {new_total_quantity} @ ${pos['avg_cost']:.2f}"
            )
        
        else:  # sell
            pos = state.positions[ticker]
            pos["quantity"] -= quantity
            pos["current_value"] = price * pos["quantity"]
            
            state.cash_balance += (trade_value - commission - slippage_amount)
            
            logger.info(
                f"{ticker}: SELL {quantity} @ ${price:.2f} | "
                f"Remaining position: {pos['quantity']}"
            )
        
        # Create executed trade record
        executed_trade = {
            "trade_id": trade_id,
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "price": price,
            "total_value": trade_value,
            "commission": commission,
            "slippage": slippage_amount,
            "confidence": float(trade_spec.get("confidence", 0.5)),
            "reason": trade_spec.get("rationale", ""),
        }
        
        return executed_trade


class PortfolioMetricsNode:
    """
    Calculate portfolio performance metrics and statistics.
    
    Computes P&L, returns, volatility, Sharpe ratio, drawdown,
    and other performance metrics based on executed trades and positions.
    """
    
    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """
        Calculate portfolio metrics.
        
        Args:
            state: Current state with positions and executed_trades
            
        Returns:
            Updated state with portfolio_metrics
        """
        if not state.trading_enabled:
            return state
        
        logger.debug("Calculating portfolio metrics")
        
        # Get initial capital
        initial_capital = float(state.trading_config.get("initial_capital", 100000.0))
        
        # Calculate total portfolio value
        invested_value = 0.0
        unrealized_pnl = 0.0
        num_positions = 0
        
        for ticker, position in state.positions.items():
            if position["quantity"] > 0:
                pos_value = position["current_value"]
                invested_value += pos_value
                
                cost_basis = position["avg_cost"] * position["quantity"]
                unrealized_pnl += (pos_value - cost_basis)
                num_positions += 1
        
        total_value = state.cash_balance + invested_value
        
        # Calculate realized P&L from closed trades
        realized_pnl = self._calculate_realized_pnl(state.executed_trades)
        
        # Calculate win rate and trade stats
        win_count, loss_count, avg_win, avg_loss = self._calculate_trade_stats(state.executed_trades)
        win_rate = (win_count / (win_count + loss_count) * 100) if (win_count + loss_count) > 0 else 0.0
        
        # Calculate volatility and returns
        return_amount = total_value - initial_capital
        return_pct = (return_amount / initial_capital) * 100 if initial_capital > 0 else 0.0
        
        # Estimate volatility (simplified)
        volatility = self._estimate_volatility(state.executed_trades)
        
        # Calculate Sharpe ratio (simplified, assuming 0% risk-free rate)
        sharpe_ratio = (return_pct / volatility) if volatility > 0 else 0.0
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown(state.executed_trades, initial_capital, state.cash_balance)
        
        # Populate metrics dictionary
        state.portfolio_metrics = {
            "total_value": total_value,
            "cash": state.cash_balance,
            "invested_value": invested_value,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": realized_pnl + unrealized_pnl,
            "return_pct": return_pct,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "total_trades": len(state.executed_trades),
            "winning_trades": win_count,
            "losing_trades": loss_count,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "num_positions": num_positions,
            "last_updated": datetime.utcnow().isoformat(),
        }
        
        logger.info(
            f"Portfolio metrics updated: "
            f"Value=${total_value:,.2f}, "
            f"Return={return_pct:.2f}%, "
            f"Trades={len(state.executed_trades)}, "
            f"WinRate={win_rate:.1f}%"
        )
        
        return state
    
    @staticmethod
    def _calculate_realized_pnl(executed_trades: List[Dict[str, Any]]) -> float:
        """
        Calculate realized P&L from all executed trades.
        
        Simplified: Uses trade price differences for buys/sells.
        """
        trade_pairs: Dict[str, List[Dict]] = {}
        
        # Group trades by ticker
        for trade in executed_trades:
            ticker = trade["ticker"]
            if ticker not in trade_pairs:
                trade_pairs[ticker] = {"buys": [], "sells": []}
            
            if trade["action"] == "buy":
                trade_pairs[ticker]["buys"].append(trade)
            else:
                trade_pairs[ticker]["sells"].append(trade)
        
        # Calculate P&L from matched pairs
        realized_pnl = 0.0
        for ticker, trades in trade_pairs.items():
            buys = sorted(trades["buys"], key=lambda t: t["timestamp"])
            sells = sorted(trades["sells"], key=lambda t: t["timestamp"])
            
            for buy in buys:
                if not sells:
                    break
                sell = sells.pop(0)
                
                quantity = min(buy["quantity"], sell["quantity"])
                pnl = (sell["price"] - buy["price"]) * quantity
                realized_pnl += pnl
        
        return realized_pnl
    
    @staticmethod
    def _calculate_trade_stats(executed_trades: List[Dict[str, Any]]) -> tuple:
        """
        Calculate trade win rate and statistics.
        
        Returns: (win_count, loss_count, avg_win, avg_loss)
        """
        if not executed_trades:
            return 0, 0, 0.0, 0.0
        
        trades_by_ticker: Dict[str, List] = {}
        
        for trade in executed_trades:
            ticker = trade["ticker"]
            if ticker not in trades_by_ticker:
                trades_by_ticker[ticker] = []
            trades_by_ticker[ticker].append(trade)
        
        winning_pnl = []
        losing_pnl = []
        
        for trades in trades_by_ticker.values():
            buys = [t for t in trades if t["action"] == "buy"]
            sells = [t for t in trades if t["action"] == "sell"]
            
            for buy in buys:
                for sell in sells:
                    pnl = (sell["price"] - buy["price"]) * min(buy["quantity"], sell["quantity"])
                    if pnl > 0:
                        winning_pnl.append(pnl)
                    else:
                        losing_pnl.append(pnl)
        
        win_count = len(winning_pnl)
        loss_count = len(losing_pnl)
        avg_win = sum(winning_pnl) / win_count if win_count > 0 else 0.0
        avg_loss = sum(losing_pnl) / loss_count if loss_count > 0 else 0.0
        
        return win_count, loss_count, avg_win, avg_loss
    
    @staticmethod
    def _estimate_volatility(executed_trades: List[Dict[str, Any]]) -> float:
        """
        Estimate portfolio volatility from trading activity.
        
        Simplified: Uses price range and trade frequency.
        Returns annualized volatility estimate.
        """
        if not executed_trades:
            return 0.15  # Default 15%
        
        # Get all prices
        prices = [t["price"] for t in executed_trades]
        
        if len(prices) < 2:
            return 0.15
        
        # Calculate simple price volatility
        avg_price = sum(prices) / len(prices)
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        
        price_range = max(prices) - min(prices)
        coeff_of_variation = std_dev / avg_price if avg_price > 0 else 0.0
        
        # Annualize (simplified: assume 252 trading days, but use actual trade count)
        daily_vol = coeff_of_variation * 0.1  # Scale down
        annualized_vol = daily_vol * (252 ** 0.5)
        
        # Clamp between reasonable bounds
        return max(0.05, min(2.0, annualized_vol))
    
    @staticmethod
    def _calculate_max_drawdown(
        executed_trades: List[Dict[str, Any]],
        initial_capital: float,
        final_cash: float
    ) -> float:
        """
        Calculate maximum drawdown from execution history.
        
        Simplified: Uses peak capital and trough based on executed trades.
        """
        if not executed_trades:
            return 0.0
        
        # Simulate portfolio value at each trade
        cumulative_pnl = 0.0
        peak_value = initial_capital
        max_dd = 0.0
        
        for trade in executed_trades:
            quantity = trade["quantity"]
            price = trade["price"]
            
            if trade["action"] == "sell":
                cumulative_pnl += (price * quantity)
            else:
                cumulative_pnl -= (price * quantity)
            
            current_value = initial_capital + cumulative_pnl
            
            if current_value > peak_value:
                peak_value = current_value
            
            DrawDown = (peak_value - current_value) / peak_value if peak_value > 0 else 0.0
            if DrawDown > max_dd:
                max_dd = DrawDown
        
        return -max_dd * 100  # Return as percentage, negative


# Export node instances for use in graph
recommendation_to_trade_node = RecommendationToTradeNode()
trade_execution_node = TradeExecutionNode()
portfolio_metrics_node = PortfolioMetricsNode()
