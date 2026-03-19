"""
Portfolio data model for trading simulation.
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Portfolio:
    """
    Represents a virtual trading portfolio with cash and stock positions.
    
    Attributes:
        portfolio_id: Unique identifier for the portfolio
        cash_balance: Available cash for trading
        positions: Dictionary mapping symbol to Position objects
        creation_timestamp: When the portfolio was created
        initial_cash_balance: Starting cash balance for performance calculations
    """
    
    portfolio_id: str
    cash_balance: Decimal
    positions: Dict[str, 'Position'] = field(default_factory=dict)
    creation_timestamp: datetime = field(default_factory=datetime.now)
    initial_cash_balance: Decimal = field(default=Decimal("0"))
    
    def __post_init__(self):
        """Initialize initial_cash_balance if not set."""
        if self.initial_cash_balance == Decimal("0"):
            self.initial_cash_balance = self.cash_balance
    
    def get_cash_balance(self) -> Decimal:
        """Returns the current cash balance."""
        return self.cash_balance
    
    def get_positions(self) -> Dict[str, 'Position']:
        """Returns all current positions."""
        return self.positions.copy()
    
    def add_position(self, symbol: str, position: 'Position') -> None:
        """
        Adds or updates a position in the portfolio.
        
        Args:
            symbol: Stock symbol
            position: Position object
        """
        self.positions[symbol] = position
    
    def remove_position(self, symbol: str) -> None:
        """
        Removes a position from the portfolio.
        
        Args:
            symbol: Stock symbol to remove
        """
        if symbol in self.positions:
            del self.positions[symbol]
    
    def update_cash(self, amount: Decimal) -> None:
        """
        Updates the cash balance by adding the specified amount.
        Can be positive (deposit/sell proceeds) or negative (buy cost).
        
        Args:
            amount: Amount to add to cash balance (can be negative)
        """
        self.cash_balance += amount
    
    def to_dict(self) -> dict:
        """
        Serializes portfolio to dictionary format.
        
        Returns:
            Dictionary representation of portfolio
        """
        # Import here to avoid circular dependency
        from .position import Position
        
        return {
            'portfolio_id': self.portfolio_id,
            'cash_balance': str(self.cash_balance),
            'initial_cash_balance': str(self.initial_cash_balance),
            'creation_timestamp': self.creation_timestamp.isoformat(),
            'positions': {
                symbol: position.to_dict()
                for symbol, position in self.positions.items()
            }
        }
    
    def to_json(self) -> str:
        """
        Serializes portfolio to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        """
        Deserializes portfolio from dictionary format.
        
        Args:
            data: Dictionary containing portfolio data
            
        Returns:
            Portfolio object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Import here to avoid circular dependency
        from .position import Position
        
        # Validate required fields
        required_fields = ['portfolio_id', 'cash_balance', 'creation_timestamp', 'initial_cash_balance']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Parse positions
        positions = {}
        if 'positions' in data:
            for symbol, position_data in data['positions'].items():
                positions[symbol] = Position.from_dict(position_data)
        
        return cls(
            portfolio_id=data['portfolio_id'],
            cash_balance=Decimal(data['cash_balance']),
            initial_cash_balance=Decimal(data['initial_cash_balance']),
            creation_timestamp=datetime.fromisoformat(data['creation_timestamp']),
            positions=positions
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Portfolio':
        """
        Deserializes portfolio from JSON string.
        
        Args:
            json_str: JSON string containing portfolio data
            
        Returns:
            Portfolio object
            
        Raises:
            ValueError: If JSON is invalid or required fields are missing
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
