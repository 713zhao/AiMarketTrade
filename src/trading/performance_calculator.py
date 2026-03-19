"""
Performance Calculator component for trading simulation.
"""

import logging
from decimal import Decimal
from typing import Dict, Optional, List
from .models.portfolio import Portfolio
from .models.trade_history import TradeHistory
from .models.trade import TradeAction
from .models.performance_report import PerformanceReport


class PerformanceCalculator:
    """
    Calculates portfolio performance metrics.
    
    Responsibilities:
    - Calculate portfolio valuation
    - Calculate realized and unrealized P&L
    - Calculate performance metrics (win rate, avg profit/loss, etc.)
    - Generate comprehensive performance reports
    """
    
    def __init__(self, portfolio: Portfolio, trade_history: TradeHistory):
        """
        Initialize Performance Calculator.
        
        Args:
            portfolio: Portfolio to calculate performance for
            trade_history: Trade history manager
        """
        self.portfolio = portfolio
        self.trade_history = trade_history
        self.logger = logging.getLogger(__name__)
    
    def _get_current_price(self, symbol: str) -> Optional[Decimal]:
        """
        Gets the most recent price for a symbol from trade history.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Most recent trade price or None if no trades found
        """
        trades = self.trade_history.get_trades_by_symbol(symbol, self.portfolio.portfolio_id)
        if not trades:
            return None
        
        # Get most recent trade
        recent_trade = max(trades, key=lambda t: t.timestamp)
        return recent_trade.price
    
    def calculate_portfolio_value(self, current_prices: Optional[Dict[str, Decimal]] = None) -> Decimal:
        """
        Calculates total portfolio value.
        
        Args:
            current_prices: Optional dict mapping symbol to current price
            
        Returns:
            Total portfolio value (cash + sum of position values)
        """
        total_value = self.portfolio.cash_balance
        
        for symbol, position in self.portfolio.positions.items():
            # Use provided price or fall back to last trade price
            if current_prices and symbol in current_prices:
                price = current_prices[symbol]
            else:
                price = self._get_current_price(symbol)
                if price is None:
                    # Use average cost basis as fallback
                    price = position.average_cost_basis
            
            total_value += position.calculate_value(price)
        
        return total_value
    
    def calculate_realized_pnl(self) -> Decimal:
        """
        Calculates realized profit/loss from closed trades.
        
        Returns:
            Total realized P&L
        """
        realized_pnl = Decimal("0")
        
        # Get all trades for this portfolio
        trades = self.trade_history.get_trades_by_portfolio(self.portfolio.portfolio_id)
        
        # Group trades by symbol to match buys with sells
        trades_by_symbol = {}
        for trade in trades:
            if trade.symbol not in trades_by_symbol:
                trades_by_symbol[trade.symbol] = []
            trades_by_symbol[trade.symbol].append(trade)
        
        # Calculate P&L for each symbol
        for symbol, symbol_trades in trades_by_symbol.items():
            # Sort by timestamp
            symbol_trades.sort(key=lambda t: t.timestamp)
            
            # Track cost basis using FIFO
            buy_queue = []  # List of (quantity, price) tuples
            
            for trade in symbol_trades:
                if trade.action == TradeAction.BUY:
                    buy_queue.append((trade.quantity, trade.price))
                else:  # SELL
                    remaining_sell_qty = trade.quantity
                    sell_price = trade.price
                    
                    # Match with buys using FIFO
                    while remaining_sell_qty > 0 and buy_queue:
                        buy_qty, buy_price = buy_queue[0]
                        
                        if buy_qty <= remaining_sell_qty:
                            # Sell entire buy lot
                            pnl = (sell_price - buy_price) * Decimal(buy_qty)
                            realized_pnl += pnl
                            remaining_sell_qty -= buy_qty
                            buy_queue.pop(0)
                        else:
                            # Partial sell of buy lot
                            pnl = (sell_price - buy_price) * Decimal(remaining_sell_qty)
                            realized_pnl += pnl
                            buy_queue[0] = (buy_qty - remaining_sell_qty, buy_price)
                            remaining_sell_qty = 0
        
        return realized_pnl
    
    def calculate_unrealized_pnl(self, current_prices: Optional[Dict[str, Decimal]] = None) -> Decimal:
        """
        Calculates unrealized profit/loss for open positions.
        
        Args:
            current_prices: Optional dict mapping symbol to current price
            
        Returns:
            Total unrealized P&L
        """
        unrealized_pnl = Decimal("0")
        
        for symbol, position in self.portfolio.positions.items():
            # Use provided price or fall back to last trade price
            if current_prices and symbol in current_prices:
                price = current_prices[symbol]
            else:
                price = self._get_current_price(symbol)
                if price is None:
                    # Skip if no price available
                    continue
            
            unrealized_pnl += position.calculate_unrealized_pnl(price)
        
        return unrealized_pnl
    
    def calculate_total_pnl(self, current_prices: Optional[Dict[str, Decimal]] = None) -> Decimal:
        """
        Calculates total profit/loss (realized + unrealized).
        
        Args:
            current_prices: Optional dict mapping symbol to current price
            
        Returns:
            Total P&L
        """
        realized = self.calculate_realized_pnl()
        unrealized = self.calculate_unrealized_pnl(current_prices)
        return realized + unrealized
    
    def calculate_pnl_percentage(self, current_prices: Optional[Dict[str, Decimal]] = None) -> Decimal:
        """
        Calculates P&L as percentage of initial cash balance.
        
        Args:
            current_prices: Optional dict mapping symbol to current price
            
        Returns:
            P&L percentage
        """
        if self.portfolio.initial_cash_balance == Decimal("0"):
            return Decimal("0")
        
        total_pnl = self.calculate_total_pnl(current_prices)
        return (total_pnl / self.portfolio.initial_cash_balance) * Decimal("100")
    
    def calculate_total_return_percentage(self, current_prices: Optional[Dict[str, Decimal]] = None) -> Decimal:
        """
        Calculates total return percentage.
        
        Args:
            current_prices: Optional dict mapping symbol to current price
            
        Returns:
            Total return percentage
        """
        if self.portfolio.initial_cash_balance == Decimal("0"):
            return Decimal("0")
        
        current_value = self.calculate_portfolio_value(current_prices)
        return ((current_value - self.portfolio.initial_cash_balance) / 
                self.portfolio.initial_cash_balance) * Decimal("100")
    
    def calculate_win_rate(self) -> Decimal:
        """
        Calculates win rate (percentage of profitable closed trades).
        
        Returns:
            Win rate percentage
        """
        trades = self.trade_history.get_trades_by_portfolio(self.portfolio.portfolio_id)
        
        # Group trades by symbol to identify closed positions
        trades_by_symbol = {}
        for trade in trades:
            if trade.symbol not in trades_by_symbol:
                trades_by_symbol[trade.symbol] = []
            trades_by_symbol[trade.symbol].append(trade)
        
        winning_trades = 0
        total_closed_trades = 0
        
        # Analyze each symbol's trades
        for symbol, symbol_trades in trades_by_symbol.items():
            symbol_trades.sort(key=lambda t: t.timestamp)
            
            buy_queue = []
            
            for trade in symbol_trades:
                if trade.action == TradeAction.BUY:
                    buy_queue.append((trade.quantity, trade.price))
                else:  # SELL
                    remaining_sell_qty = trade.quantity
                    sell_price = trade.price
                    
                    while remaining_sell_qty > 0 and buy_queue:
                        buy_qty, buy_price = buy_queue[0]
                        
                        if buy_qty <= remaining_sell_qty:
                            # Complete trade
                            pnl = (sell_price - buy_price) * Decimal(buy_qty)
                            if pnl > Decimal("0"):
                                winning_trades += 1
                            total_closed_trades += 1
                            remaining_sell_qty -= buy_qty
                            buy_queue.pop(0)
                        else:
                            # Partial sell
                            pnl = (sell_price - buy_price) * Decimal(remaining_sell_qty)
                            if pnl > Decimal("0"):
                                winning_trades += 1
                            total_closed_trades += 1
                            buy_queue[0] = (buy_qty - remaining_sell_qty, buy_price)
                            remaining_sell_qty = 0
        
        if total_closed_trades == 0:
            return Decimal("0")
        
        return (Decimal(winning_trades) / Decimal(total_closed_trades)) * Decimal("100")
    
    def calculate_average_profit_per_win(self) -> Decimal:
        """
        Calculates average profit per winning trade.
        
        Returns:
            Average profit per win
        """
        trades = self.trade_history.get_trades_by_portfolio(self.portfolio.portfolio_id)
        
        trades_by_symbol = {}
        for trade in trades:
            if trade.symbol not in trades_by_symbol:
                trades_by_symbol[trade.symbol] = []
            trades_by_symbol[trade.symbol].append(trade)
        
        winning_profits = []
        
        for symbol, symbol_trades in trades_by_symbol.items():
            symbol_trades.sort(key=lambda t: t.timestamp)
            buy_queue = []
            
            for trade in symbol_trades:
                if trade.action == TradeAction.BUY:
                    buy_queue.append((trade.quantity, trade.price))
                else:
                    remaining_sell_qty = trade.quantity
                    sell_price = trade.price
                    
                    while remaining_sell_qty > 0 and buy_queue:
                        buy_qty, buy_price = buy_queue[0]
                        
                        if buy_qty <= remaining_sell_qty:
                            pnl = (sell_price - buy_price) * Decimal(buy_qty)
                            if pnl > Decimal("0"):
                                winning_profits.append(pnl)
                            remaining_sell_qty -= buy_qty
                            buy_queue.pop(0)
                        else:
                            pnl = (sell_price - buy_price) * Decimal(remaining_sell_qty)
                            if pnl > Decimal("0"):
                                winning_profits.append(pnl)
                            buy_queue[0] = (buy_qty - remaining_sell_qty, buy_price)
                            remaining_sell_qty = 0
        
        if not winning_profits:
            return Decimal("0")
        
        return sum(winning_profits) / Decimal(len(winning_profits))
    
    def calculate_average_loss_per_loss(self) -> Decimal:
        """
        Calculates average loss per losing trade.
        
        Returns:
            Average loss per loss (as positive number)
        """
        trades = self.trade_history.get_trades_by_portfolio(self.portfolio.portfolio_id)
        
        trades_by_symbol = {}
        for trade in trades:
            if trade.symbol not in trades_by_symbol:
                trades_by_symbol[trade.symbol] = []
            trades_by_symbol[trade.symbol].append(trade)
        
        losing_losses = []
        
        for symbol, symbol_trades in trades_by_symbol.items():
            symbol_trades.sort(key=lambda t: t.timestamp)
            buy_queue = []
            
            for trade in symbol_trades:
                if trade.action == TradeAction.BUY:
                    buy_queue.append((trade.quantity, trade.price))
                else:
                    remaining_sell_qty = trade.quantity
                    sell_price = trade.price
                    
                    while remaining_sell_qty > 0 and buy_queue:
                        buy_qty, buy_price = buy_queue[0]
                        
                        if buy_qty <= remaining_sell_qty:
                            pnl = (sell_price - buy_price) * Decimal(buy_qty)
                            if pnl < Decimal("0"):
                                losing_losses.append(abs(pnl))
                            remaining_sell_qty -= buy_qty
                            buy_queue.pop(0)
                        else:
                            pnl = (sell_price - buy_price) * Decimal(remaining_sell_qty)
                            if pnl < Decimal("0"):
                                losing_losses.append(abs(pnl))
                            buy_queue[0] = (buy_qty - remaining_sell_qty, buy_price)
                            remaining_sell_qty = 0
        
        if not losing_losses:
            return Decimal("0")
        
        return sum(losing_losses) / Decimal(len(losing_losses))
    
    def calculate_maximum_drawdown(self) -> Decimal:
        """
        Calculates maximum drawdown (largest peak-to-trough decline).
        
        Returns:
            Maximum drawdown as percentage (negative value)
        """
        trades = self.trade_history.get_trades_by_portfolio(self.portfolio.portfolio_id)
        
        if not trades:
            return Decimal("0")
        
        # Sort trades by timestamp
        trades.sort(key=lambda t: t.timestamp)
        
        # Track portfolio value over time
        cash = self.portfolio.initial_cash_balance
        positions = {}
        peak_value = cash
        max_drawdown = Decimal("0")
        
        for trade in trades:
            if trade.action == TradeAction.BUY:
                cost = trade.price * Decimal(trade.quantity)
                cash -= cost
                if trade.symbol in positions:
                    positions[trade.symbol] = (
                        positions[trade.symbol][0] + trade.quantity,
                        trade.price
                    )
                else:
                    positions[trade.symbol] = (trade.quantity, trade.price)
            else:  # SELL
                proceeds = trade.price * Decimal(trade.quantity)
                cash += proceeds
                if trade.symbol in positions:
                    qty, _ = positions[trade.symbol]
                    new_qty = qty - trade.quantity
                    if new_qty <= 0:
                        del positions[trade.symbol]
                    else:
                        positions[trade.symbol] = (new_qty, positions[trade.symbol][1])
            
            # Calculate current portfolio value
            current_value = cash
            for symbol, (qty, price) in positions.items():
                current_value += Decimal(qty) * price
            
            # Update peak and drawdown
            if current_value > peak_value:
                peak_value = current_value
            else:
                drawdown = ((current_value - peak_value) / peak_value) * Decimal("100")
                if drawdown < max_drawdown:
                    max_drawdown = drawdown
        
        return max_drawdown
    
    def get_trade_statistics(self) -> Dict:
        """
        Gets trade statistics.
        
        Returns:
            Dictionary with total_trades and open_positions count
        """
        trades = self.trade_history.get_trades_by_portfolio(self.portfolio.portfolio_id)
        return {
            'total_trades': len(trades),
            'open_positions': len(self.portfolio.positions)
        }
    
    def generate_performance_report(self, current_prices: Optional[Dict[str, Decimal]] = None) -> PerformanceReport:
        """
        Generates comprehensive performance report.
        
        Args:
            current_prices: Optional dict mapping symbol to current price
            
        Returns:
            PerformanceReport object
        """
        # Calculate all metrics
        portfolio_value = self.calculate_portfolio_value(current_prices)
        realized_pnl = self.calculate_realized_pnl()
        unrealized_pnl = self.calculate_unrealized_pnl(current_prices)
        total_pnl = realized_pnl + unrealized_pnl
        total_return_pct = self.calculate_total_return_percentage(current_prices)
        win_rate = self.calculate_win_rate()
        avg_profit = self.calculate_average_profit_per_win()
        avg_loss = self.calculate_average_loss_per_loss()
        max_drawdown = self.calculate_maximum_drawdown()
        stats = self.get_trade_statistics()
        
        # Get open positions details
        open_positions_list = []
        for symbol, position in self.portfolio.positions.items():
            if current_prices and symbol in current_prices:
                price = current_prices[symbol]
            else:
                price = self._get_current_price(symbol)
                if price is None:
                    price = position.average_cost_basis
            
            open_positions_list.append({
                'symbol': symbol,
                'quantity': position.quantity,
                'average_cost': float(position.average_cost_basis),
                'current_price': float(price),
                'current_value': float(position.calculate_value(price)),
                'unrealized_pnl': float(position.calculate_unrealized_pnl(price))
            })
        
        # Get recent trades
        all_trades = self.trade_history.get_trades_by_portfolio(self.portfolio.portfolio_id)
        all_trades.sort(key=lambda t: t.timestamp, reverse=True)
        recent_trades = []
        for trade in all_trades[:10]:
            recent_trades.append({
                'timestamp': trade.timestamp.isoformat(),
                'action': trade.action.value,
                'symbol': trade.symbol,
                'quantity': trade.quantity,
                'price': float(trade.price)
            })
        
        return PerformanceReport(
            portfolio_value=portfolio_value,
            cash_balance=self.portfolio.cash_balance,
            total_positions=stats['open_positions'],
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_pnl=total_pnl,
            total_return_pct=total_return_pct,
            win_rate=win_rate,
            avg_profit_per_win=avg_profit,
            avg_loss_per_loss=avg_loss,
            max_drawdown=max_drawdown,
            total_trades=stats['total_trades'],
            open_positions_list=open_positions_list,
            recent_trades=recent_trades
        )
