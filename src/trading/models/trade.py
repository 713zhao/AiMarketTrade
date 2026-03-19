"""
Trade data model for trading simulation.
"""

import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


class TradeAction(Enum):
    """Type of trade action."""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Trade:
    """
    Represents a single trade transaction.
    
    Attributes:
        trade_id: Unique identifier for the trade
        portfolio_id: ID of the portfolio this trade belongs to
        symbol: Stock symbol
        action: BUY or SELL
        quantity: Number of shares traded
        price: Price per share
        timestamp: When the trade was executed
        recommendation_id: Optional ID of the recommendation that triggered this trade
        stock_name: Optional human-readable stock name
        rationale: Optional reason for the trade decision
    """
    
    trade_id: str
    portfolio_id: str
    symbol: str
    action: TradeAction
    quantity: int
    price: Decimal
    timestamp: datetime = field(default_factory=datetime.now)
    recommendation_id: Optional[str] = None
    stock_name: Optional[str] = None
    rationale: Optional[str] = None
    
    def calculate_total_cost(self) -> Decimal:
        """
        Calculates the total cost of a buy trade.
        
        Returns:
            Total cost: quantity × price
        """
        return Decimal(self.quantity) * self.price
    
    def calculate_proceeds(self) -> Decimal:
        """
        Calculates the total proceeds of a sell trade.
        
        Returns:
            Total proceeds: quantity × price
        """
        return Decimal(self.quantity) * self.price
    
    def to_dict(self) -> dict:
        """
        Serializes trade to dictionary format.
        
        Returns:
            Dictionary representation of trade
        """
        return {
            'trade_id': self.trade_id,
            'portfolio_id': self.portfolio_id,
            'symbol': self.symbol,
            'action': self.action.value,
            'quantity': self.quantity,
            'price': str(self.price),
            'timestamp': self.timestamp.isoformat(),
            'recommendation_id': self.recommendation_id,
            'stock_name': self.stock_name,
            'rationale': self.rationale
        }
    
    def to_json(self) -> str:
        """
        Serializes trade to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Trade':
        """
        Deserializes trade from dictionary format.
        
        Args:
            data: Dictionary containing trade data
            
        Returns:
            Trade object
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['trade_id', 'portfolio_id', 'symbol', 'action', 'quantity', 'price', 'timestamp']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return cls(
            trade_id=data['trade_id'],
            portfolio_id=data['portfolio_id'],
            symbol=data['symbol'],
            action=TradeAction(data['action']),
            quantity=data['quantity'],
            price=Decimal(data['price']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            recommendation_id=data.get('recommendation_id'),
            stock_name=data.get('stock_name'),
            rationale=data.get('rationale')
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Trade':
        """
        Deserializes trade from JSON string.
        
        Args:
            json_str: JSON string containing trade data
            
        Returns:
            Trade object
            
        Raises:
            ValueError: If JSON is invalid or required fields are missing
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
