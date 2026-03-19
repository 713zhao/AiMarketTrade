"""
Trade Executor component for trading simulation.
"""

import logging
import uuid
import re
from decimal import Decimal
from typing import Optional, Dict
from datetime import datetime

from .models.portfolio import Portfolio
from .models.position import Position
from .models.trade import Trade, TradeAction
from .models.trade_history import TradeHistory


class TradeExecutor:
    """
    Executes buy and sell orders for a trading portfolio.
    
    Responsibilities:
    - Validate trade parameters
    - Execute buy orders with cash balance validation
    - Execute sell orders with position validation
    - Update portfolio state
    - Record trades in history
    - Calculate position sizing
    """
    
    def __init__(self, portfolio: Portfolio, trade_history: TradeHistory, config: Optional[Dict] = None):
        """
        Initialize Trade Executor.
        
        Args:
            portfolio: Portfolio to execute trades for
            trade_history: Trade history manager
            config: Optional configuration dictionary
        """
        self.portfolio = portfolio
        self.trade_history = trade_history
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    def _validate_symbol(self, symbol: str) -> None:
        """
        Validates stock symbol format.
        
        Args:
            symbol: Stock symbol to validate
            
        Raises:
            ValueError: If symbol format is invalid
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Invalid symbol format")
        
        # Symbol should be alphanumeric with optional dots and hyphens
        if not re.match(r'^[A-Z0-9.-]+$', symbol.upper()):
            raise ValueError("Invalid symbol format")
    
    def _validate_price(self, price: Decimal) -> None:
        """
        Validates trade price.
        
        Args:
            price: Price to validate
            
        Raises:
            ValueError: If price is not positive
        """
        if price <= Decimal("0"):
            raise ValueError("Price must be positive")
    
    def _validate_quantity(self, quantity: int) -> None:
        """
        Validates trade quantity.
        
        Args:
            quantity: Quantity to validate
            
        Raises:
            ValueError: If quantity is not positive
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    
    def execute_buy_order(
        self,
        symbol: str,
        quantity: int,
        price: Decimal,
        recommendation_id: Optional[str] = None,
        stock_name: Optional[str] = None,
        rationale: Optional[str] = None
    ) -> Trade:
        """
        Executes a buy order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares to buy
            price: Price per share
            recommendation_id: Optional recommendation ID
            stock_name: Optional human-readable stock name
            rationale: Optional reason for the trade
            
        Returns:
            Trade object representing the executed trade
            
        Raises:
            ValueError: If validation fails or insufficient cash
        """
        # Validate inputs
        self._validate_symbol(symbol)
        self._validate_quantity(quantity)
        self._validate_price(price)
        
        # Calculate total cost
        total_cost = Decimal(quantity) * price
        
        # Validate sufficient cash balance
        if self.portfolio.cash_balance < total_cost:
            raise ValueError("Insufficient cash balance")
        
        # Create or update position
        symbol_upper = symbol.upper()
        if symbol_upper in self.portfolio.positions:
            # Update existing position
            position = self.portfolio.positions[symbol_upper]
            position.update_average_cost(quantity, price)
        else:
            # Create new position
            position = Position(
                symbol=symbol_upper,
                quantity=quantity,
                average_cost_basis=price
            )
            self.portfolio.add_position(symbol_upper, position)
        
        # Deduct cash
        self.portfolio.update_cash(-total_cost)
        
        # Create trade record
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            portfolio_id=self.portfolio.portfolio_id,
            symbol=symbol_upper,
            action=TradeAction.BUY,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
            recommendation_id=recommendation_id,
            stock_name=stock_name,
            rationale=rationale
        )
        
        # Record in history
        self.trade_history.add_trade(trade)
        
        # Log with stock name if available
        name_str = f" ({stock_name})" if stock_name else ""
        self.logger.info(f"Executed BUY: {quantity} {symbol_upper}{name_str} @ ${price}")
        
        return trade
    
    def execute_sell_order(
        self,
        symbol: str,
        quantity: int,
        price: Decimal,
        recommendation_id: Optional[str] = None,
        stock_name: Optional[str] = None,
        rationale: Optional[str] = None
    ) -> Trade:
        """
        Executes a sell order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares to sell
            price: Price per share
            recommendation_id: Optional recommendation ID
            stock_name: Optional human-readable stock name
            rationale: Optional reason for the trade
            
        Returns:
            Trade object representing the executed trade
            
        Raises:
            ValueError: If validation fails or insufficient position
        """
        # Validate inputs
        self._validate_symbol(symbol)
        self._validate_quantity(quantity)
        self._validate_price(price)
        
        symbol_upper = symbol.upper()
        
        # Validate position exists
        if symbol_upper not in self.portfolio.positions:
            raise ValueError("Position not found")
        
        position = self.portfolio.positions[symbol_upper]
        
        # Validate sufficient quantity
        if position.quantity < quantity:
            raise ValueError("Insufficient position quantity")
        
        # Calculate proceeds
        proceeds = Decimal(quantity) * price
        
        # Update position
        position.quantity -= quantity
        
        # Remove position if quantity reaches zero
        if position.quantity == 0:
            self.portfolio.remove_position(symbol_upper)
        
        # Add proceeds to cash
        self.portfolio.update_cash(proceeds)
        
        # Create trade record
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            portfolio_id=self.portfolio.portfolio_id,
            symbol=symbol_upper,
            action=TradeAction.SELL,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
            recommendation_id=recommendation_id,
            stock_name=stock_name,
            rationale=rationale
        )
        
        # Record in history
        self.trade_history.add_trade(trade)
        
        # Log with stock name if available
        name_str = f" ({stock_name})" if stock_name else ""
        self.logger.info(f"Executed SELL: {quantity} {symbol_upper}{name_str} @ ${price}")
        
        return trade
    
    def _calculate_buy_quantity(
        self,
        price: Decimal,
        strategy: str,
        strategy_value: Decimal,
        portfolio_value: Decimal
    ) -> int:
        """
        Calculates buy quantity based on position sizing strategy.
        
        Args:
            price: Price per share
            strategy: "fixed_amount" or "percentage"
            strategy_value: Fixed amount or percentage value
            portfolio_value: Current total portfolio value
            
        Returns:
            Number of shares to buy (rounded down to whole shares)
        """
        if strategy == "fixed_amount":
            # Quantity = fixed_amount / price
            quantity = strategy_value / price
        elif strategy == "percentage":
            # Quantity = (portfolio_value * percentage) / price
            quantity = (portfolio_value * strategy_value) / price
        else:
            raise ValueError(f"Unknown position sizing strategy: {strategy}")
        
        # Round down to nearest whole share
        quantity_int = int(quantity)
        
        # Return 0 if less than 1 share
        return max(0, quantity_int)
    
    def execute_recommendation(
        self,
        recommendation,
        confidence_threshold: float,
        sizing_strategy: str,
        sizing_value: Decimal
    ) -> Optional[Trade]:
        """
        Executes a trade based on a recommendation.
        
        Args:
            recommendation: StockRecommendation object
            confidence_threshold: Minimum confidence to execute
            sizing_strategy: Position sizing strategy
            sizing_value: Strategy value (amount or percentage)
            
        Returns:
            Trade object if executed, None otherwise
        """
        from stock_market_analysis.models import RecommendationType
        
        # Check confidence threshold
        if recommendation.confidence_score < confidence_threshold:
            self.logger.debug(
                f"Skipping {recommendation.symbol}: confidence {recommendation.confidence_score:.2f} "
                f"below threshold {confidence_threshold:.2f}"
            )
            return None
        
        # Get price from recommendation
        price = recommendation.target_price
        if price is None or price <= Decimal("0"):
            self.logger.warning(f"Invalid price for {recommendation.symbol}, skipping")
            return None
        
        # Handle based on recommendation type
        if recommendation.recommendation_type == RecommendationType.BUY:
            # Calculate portfolio value for percentage sizing
            portfolio_value = self.portfolio.cash_balance
            for pos in self.portfolio.positions.values():
                portfolio_value += pos.calculate_value(price)
            
            # Calculate quantity
            quantity = self._calculate_buy_quantity(
                price, sizing_strategy, sizing_value, portfolio_value
            )
            
            if quantity == 0:
                self.logger.debug(f"Calculated quantity is 0 for {recommendation.symbol}, skipping")
                return None
            
            # Calculate cost
            total_cost = Decimal(quantity) * price
            
            # Check if we have enough cash
            if total_cost > self.portfolio.cash_balance:
                self.logger.debug(
                    f"Insufficient cash for {recommendation.symbol}: "
                    f"need ${total_cost}, have ${self.portfolio.cash_balance}"
                )
                return None
            
            # Execute buy
            try:
                return self.execute_buy_order(
                    recommendation.symbol,
                    quantity,
                    price,
                    recommendation_id=getattr(recommendation, 'recommendation_id', None),
                    stock_name=getattr(recommendation, 'name', None),
                    rationale=getattr(recommendation, 'rationale', None)
                )
            except ValueError as e:
                self.logger.warning(f"Failed to execute BUY for {recommendation.symbol}: {e}")
                return None
        
        elif recommendation.recommendation_type == RecommendationType.SELL:
            # Check if we have a position
            symbol_upper = recommendation.symbol.upper()
            if symbol_upper not in self.portfolio.positions:
                self.logger.debug(f"No position in {recommendation.symbol}, skipping SELL")
                return None
            
            # Sell entire position
            position = self.portfolio.positions[symbol_upper]
            quantity = position.quantity
            
            # Execute sell
            try:
                return self.execute_sell_order(
                    recommendation.symbol,
                    quantity,
                    price,
                    recommendation_id=getattr(recommendation, 'recommendation_id', None),
                    stock_name=getattr(recommendation, 'name', None),
                    rationale=getattr(recommendation, 'rationale', None)
                )
            except ValueError as e:
                self.logger.warning(f"Failed to execute SELL for {recommendation.symbol}: {e}")
                return None
        
        else:  # HOLD
            self.logger.debug(f"HOLD recommendation for {recommendation.symbol}, no action")
            return None
