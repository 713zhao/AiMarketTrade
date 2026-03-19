"""
Position data model for trading simulation.
"""

from decimal import Decimal
from dataclasses import dataclass


@dataclass
class Position:
    """
    Represents a stock position in a portfolio.
    
    Attributes:
        symbol: Stock symbol
        quantity: Number of shares held
        average_cost_basis: Average cost per share
    """
    
    symbol: str
    quantity: int
    average_cost_basis: Decimal
    
    def update_average_cost(self, additional_quantity: int, purchase_price: Decimal) -> None:
        """
        Updates the average cost basis when adding shares.
        
        Formula: new_avg = (current_total_cost + new_cost) / (current_qty + new_qty)
        
        Args:
            additional_quantity: Number of shares being added
            purchase_price: Price per share of new purchase
        """
        current_total_cost = self.average_cost_basis * Decimal(self.quantity)
        new_cost = purchase_price * Decimal(additional_quantity)
        new_total_quantity = self.quantity + additional_quantity
        
        self.average_cost_basis = (current_total_cost + new_cost) / Decimal(new_total_quantity)
        self.quantity = new_total_quantity
    
    def calculate_value(self, current_price: Decimal) -> Decimal:
        """
        Calculates the current market value of the position.
        
        Args:
            current_price: Current market price per share
            
        Returns:
            Total position value (quantity × current_price)
        """
        return Decimal(self.quantity) * current_price
    
    def calculate_unrealized_pnl(self, current_price: Decimal) -> Decimal:
        """
        Calculates unrealized profit/loss for the position.
        
        Args:
            current_price: Current market price per share
            
        Returns:
            Unrealized P&L: (current_price - average_cost) × quantity
        """
        return (current_price - self.average_cost_basis) * Decimal(self.quantity)
    
    def to_dict(self) -> dict:
        """
        Serializes position to dictionary format.
        
        Returns:
            Dictionary representation of position
        """
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'average_cost_basis': str(self.average_cost_basis)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Position':
        """
        Deserializes position from dictionary format.
        
        Args:
            data: Dictionary containing position data
            
        Returns:
            Position object
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['symbol', 'quantity', 'average_cost_basis']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return cls(
            symbol=data['symbol'],
            quantity=data['quantity'],
            average_cost_basis=Decimal(data['average_cost_basis'])
        )
