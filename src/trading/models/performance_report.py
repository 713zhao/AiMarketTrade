"""
Performance report data model for trading simulation.
"""

import json
from decimal import Decimal
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class PerformanceReport:
    """
    Comprehensive performance report for a trading portfolio.
    
    Attributes:
        portfolio_value: Current total portfolio value
        cash_balance: Current cash balance
        total_positions: Number of open positions
        realized_pnl: Realized profit/loss from closed trades
        unrealized_pnl: Unrealized profit/loss from open positions
        total_pnl: Total profit/loss (realized + unrealized)
        total_return_pct: Total return percentage
        win_rate: Percentage of profitable trades
        avg_profit_per_win: Average profit per winning trade
        avg_loss_per_loss: Average loss per losing trade
        max_drawdown: Maximum peak-to-trough decline
        total_trades: Total number of trades executed
        open_positions_list: List of open positions with details
        recent_trades: List of recent trades
    """
    
    portfolio_value: Decimal
    cash_balance: Decimal
    total_positions: int
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    total_return_pct: Decimal
    win_rate: Decimal
    avg_profit_per_win: Decimal
    avg_loss_per_loss: Decimal
    max_drawdown: Decimal
    total_trades: int
    open_positions_list: List[Dict] = field(default_factory=list)
    recent_trades: List[Dict] = field(default_factory=list)
    
    def to_json(self) -> str:
        """
        Exports report as JSON string.
        
        Returns:
            JSON string representation
        """
        data = {
            'portfolio_summary': {
                'portfolio_value': str(self.portfolio_value),
                'cash_balance': str(self.cash_balance),
                'total_positions': self.total_positions
            },
            'pnl_summary': {
                'realized_pnl': str(self.realized_pnl),
                'unrealized_pnl': str(self.unrealized_pnl),
                'total_pnl': str(self.total_pnl),
                'total_return_pct': str(self.total_return_pct)
            },
            'trade_statistics': {
                'total_trades': self.total_trades,
                'win_rate': str(self.win_rate),
                'avg_profit_per_win': str(self.avg_profit_per_win),
                'avg_loss_per_loss': str(self.avg_loss_per_loss),
                'max_drawdown': str(self.max_drawdown)
            },
            'open_positions': self.open_positions_list,
            'recent_trades': self.recent_trades
        }
        return json.dumps(data, indent=2)
    
    def to_text(self) -> str:
        """
        Exports report as formatted text.
        
        Returns:
            Human-readable text representation
        """
        lines = [
            "=" * 60,
            "TRADING PERFORMANCE REPORT",
            "=" * 60,
            "",
            "PORTFOLIO SUMMARY",
            "-" * 60,
            f"Total Value:        ${self.portfolio_value:,.2f}",
            f"Cash Balance:       ${self.cash_balance:,.2f}",
            f"Open Positions:     {self.total_positions}",
            "",
            "PROFIT & LOSS",
            "-" * 60,
            f"Realized P&L:       ${self.realized_pnl:,.2f}",
            f"Unrealized P&L:     ${self.unrealized_pnl:,.2f}",
            f"Total P&L:          ${self.total_pnl:,.2f}",
            f"Total Return:       {self.total_return_pct:.2f}%",
            "",
            "TRADE STATISTICS",
            "-" * 60,
            f"Total Trades:       {self.total_trades}",
            f"Win Rate:           {self.win_rate:.2f}%",
            f"Avg Profit/Win:     ${self.avg_profit_per_win:,.2f}",
            f"Avg Loss/Loss:      ${self.avg_loss_per_loss:,.2f}",
            f"Max Drawdown:       {self.max_drawdown:.2f}%",
            ""
        ]
        
        if self.open_positions_list:
            lines.extend([
                "OPEN POSITIONS",
                "-" * 60
            ])
            for pos in self.open_positions_list:
                lines.append(
                    f"{pos['symbol']:8} | Qty: {pos['quantity']:6} | "
                    f"Value: ${pos['current_value']:>10,.2f} | "
                    f"P&L: ${pos['unrealized_pnl']:>10,.2f}"
                )
            lines.append("")
        
        if self.recent_trades:
            lines.extend([
                "RECENT TRADES (Last 10)",
                "-" * 60
            ])
            for trade in self.recent_trades:
                lines.append(
                    f"{trade['timestamp'][:10]} | {trade['action']:4} | "
                    f"{trade['symbol']:8} | Qty: {trade['quantity']:6} | "
                    f"Price: ${trade['price']:>8,.2f}"
                )
            lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)
