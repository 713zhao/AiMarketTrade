"""
Trade history persistence for trading simulation.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional
from .trade import Trade, TradeAction


class TradeHistory:
    """
    Manages persistent storage of trade records.
    
    Stores trades in JSON format with atomic writes to prevent data corruption.
    """
    
    def __init__(self, storage_path: str = "data/trade_history.json"):
        """
        Initialize trade history manager.
        
        Args:
            storage_path: Path to JSON file for storing trades
        """
        self.storage_path = Path(storage_path)
        self.logger = logging.getLogger(__name__)
        self._trades: List[Trade] = []
        
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing trades
        self._load_trades()
    
    def add_trade(self, trade: Trade) -> None:
        """
        Adds a trade to history and persists to disk.
        
        Args:
            trade: Trade object to add
        """
        self._trades.append(trade)
        self._save_trades()
        
        # Log with stock name if available
        name_str = f" ({trade.stock_name})" if trade.stock_name else ""
        self.logger.info(f"Trade recorded: {trade.action.value} {trade.quantity} {trade.symbol}{name_str} @ {trade.price}")
    
    def get_trades_by_portfolio(self, portfolio_id: str) -> List[Trade]:
        """
        Retrieves all trades for a specific portfolio.
        
        Args:
            portfolio_id: Portfolio ID to filter by
            
        Returns:
            List of trades for the portfolio
        """
        return [trade for trade in self._trades if trade.portfolio_id == portfolio_id]
    
    def get_trades_by_symbol(self, symbol: str, portfolio_id: Optional[str] = None) -> List[Trade]:
        """
        Retrieves all trades for a specific symbol.
        
        Args:
            symbol: Stock symbol to filter by
            portfolio_id: Optional portfolio ID to further filter
            
        Returns:
            List of trades for the symbol
        """
        trades = [trade for trade in self._trades if trade.symbol == symbol]
        if portfolio_id:
            trades = [trade for trade in trades if trade.portfolio_id == portfolio_id]
        return trades
    
    def get_trades_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        portfolio_id: Optional[str] = None
    ) -> List[Trade]:
        """
        Retrieves trades within a date range.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            portfolio_id: Optional portfolio ID to filter
            
        Returns:
            List of trades within the date range
        """
        trades = [
            trade for trade in self._trades
            if start_date <= trade.timestamp <= end_date
        ]
        if portfolio_id:
            trades = [trade for trade in trades if trade.portfolio_id == portfolio_id]
        return trades
    
    def get_trades_by_action(
        self, 
        action: TradeAction,
        portfolio_id: Optional[str] = None
    ) -> List[Trade]:
        """
        Retrieves trades filtered by action type.
        
        Args:
            action: Trade action (BUY or SELL)
            portfolio_id: Optional portfolio ID to filter
            
        Returns:
            List of trades matching the action
        """
        trades = [trade for trade in self._trades if trade.action == action]
        if portfolio_id:
            trades = [trade for trade in trades if trade.portfolio_id == portfolio_id]
        return trades
    
    def get_all_trades(self, portfolio_id: Optional[str] = None) -> List[Trade]:
        """
        Retrieves all trades, optionally filtered by portfolio.
        
        Args:
            portfolio_id: Optional portfolio ID to filter
            
        Returns:
            List of all trades
        """
        if portfolio_id:
            return self.get_trades_by_portfolio(portfolio_id)
        return self._trades.copy()
    
    def _load_trades(self) -> None:
        """Loads trades from disk."""
        if not self.storage_path.exists():
            self.logger.info(f"No existing trade history found at {self.storage_path}")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self._trades = [Trade.from_dict(trade_data) for trade_data in data]
            self.logger.info(f"Loaded {len(self._trades)} trades from {self.storage_path}")
        except Exception as e:
            self.logger.error(f"Failed to load trade history: {e}")
            self._trades = []
    
    def _save_trades(self) -> None:
        """Saves trades to disk with atomic write."""
        try:
            # Write to temporary file first
            temp_path = self.storage_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                data = [trade.to_dict() for trade in self._trades]
                json.dump(data, f, indent=2)
            
            # Atomic rename
            temp_path.replace(self.storage_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save trade history: {e}")
            raise
