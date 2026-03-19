"""
Trading Simulator component for trading simulation.
"""

import logging
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional

from .models.portfolio import Portfolio
from .models.trade import Trade
from .models.trade_history import TradeHistory
from .models.performance_report import PerformanceReport
from .trade_executor import TradeExecutor
from .performance_calculator import PerformanceCalculator


class TradingSimulator:
    """
    Main trading simulation system.
    
    Responsibilities:
    - Create and manage portfolios
    - Handle cash deposits
    - Execute trades
    - Process recommendations
    - Generate performance reports
    - Persist portfolio state
    """
    
    MAX_CASH_BALANCE = Decimal("999999999.99")
    
    def __init__(self, config_manager=None):
        """
        Initialize Trading Simulator.
        
        Args:
            config_manager: Optional ConfigurationManager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize trade history (automatically loads from disk)
        self.trade_history = TradeHistory()
        
        # Portfolio storage
        self.portfolios: Dict[str, Portfolio] = {}
        
        self.logger.info("Trading Simulator initialized")
    
    def create_portfolio(self, initial_cash_balance: Decimal) -> str:
        """
        Creates a new portfolio.
        
        Args:
            initial_cash_balance: Starting cash balance
            
        Returns:
            Portfolio ID
            
        Raises:
            ValueError: If initial cash is invalid
        """
        # Validate initial cash balance
        if initial_cash_balance <= Decimal("0"):
            raise ValueError("Initial cash balance must be positive")
        
        if initial_cash_balance > self.MAX_CASH_BALANCE:
            raise ValueError(f"Initial cash balance cannot exceed {self.MAX_CASH_BALANCE}")
        
        # Generate unique portfolio ID
        portfolio_id = str(uuid.uuid4())
        
        # Create portfolio
        portfolio = Portfolio(
            portfolio_id=portfolio_id,
            cash_balance=initial_cash_balance,
            initial_cash_balance=initial_cash_balance
        )
        
        # Store portfolio
        self.portfolios[portfolio_id] = portfolio
        
        self.logger.info(f"Created portfolio {portfolio_id} with ${initial_cash_balance}")
        
        return portfolio_id
    
    def deposit_cash(self, portfolio_id: str, amount: Decimal) -> None:
        """
        Deposits cash into a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            amount: Amount to deposit
            
        Raises:
            ValueError: If amount is invalid or portfolio not found
        """
        # Validate amount
        if amount <= Decimal("0"):
            raise ValueError("Deposit amount must be positive")
        
        # Get portfolio
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        portfolio = self.portfolios[portfolio_id]
        
        # Validate new balance won't exceed maximum
        new_balance = portfolio.cash_balance + amount
        if new_balance > self.MAX_CASH_BALANCE:
            raise ValueError(f"Deposit would exceed maximum cash balance of {self.MAX_CASH_BALANCE}")
        
        # Update cash balance
        portfolio.update_cash(amount)
        
        self.logger.info(f"Deposited ${amount} to portfolio {portfolio_id}")
    
    def save_portfolio(self, portfolio_id: str, filepath: str) -> None:
        """
        Saves portfolio state to file.
        
        Args:
            portfolio_id: Portfolio ID
            filepath: Path to save file
            
        Raises:
            ValueError: If portfolio not found
        """
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        portfolio = self.portfolios[portfolio_id]
        
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(filepath, 'w') as f:
            f.write(portfolio.to_json())
        
        self.logger.info(f"Saved portfolio {portfolio_id} to {filepath}")
    
    def load_portfolio(self, filepath: str) -> str:
        """
        Loads portfolio state from file.
        
        Args:
            filepath: Path to load file
            
        Returns:
            Portfolio ID
            
        Raises:
            ValueError: If file is invalid or required fields missing
        """
        try:
            with open(filepath, 'r') as f:
                json_str = f.read()
            
            portfolio = Portfolio.from_json(json_str)
            
            # Store portfolio
            self.portfolios[portfolio.portfolio_id] = portfolio
            
            self.logger.info(f"Loaded portfolio {portfolio.portfolio_id} from {filepath}")
            
            return portfolio.portfolio_id
            
        except Exception as e:
            raise ValueError(f"Failed to load portfolio: {e}")
    
    def execute_trade(
        self,
        portfolio_id: str,
        symbol: str,
        action: str,
        quantity: int,
        price: Decimal
    ) -> Trade:
        """
        Executes a manual trade.
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            action: "BUY" or "SELL"
            quantity: Number of shares
            price: Price per share
            
        Returns:
            Trade object
            
        Raises:
            ValueError: If portfolio not found or trade fails
        """
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        portfolio = self.portfolios[portfolio_id]
        executor = TradeExecutor(portfolio, self.trade_history)
        
        if action.upper() == "BUY":
            return executor.execute_buy_order(symbol, quantity, price)
        elif action.upper() == "SELL":
            return executor.execute_sell_order(symbol, quantity, price)
        else:
            raise ValueError(f"Invalid action: {action}. Must be BUY or SELL")
    
    def process_recommendation(self, portfolio_id: str, recommendation) -> Optional[Trade]:
        """
        Processes a recommendation and executes trade if appropriate.
        
        Args:
            portfolio_id: Portfolio ID
            recommendation: StockRecommendation object
            
        Returns:
            Trade object if executed, None otherwise
            
        Raises:
            ValueError: If portfolio not found or configuration missing
        """
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        portfolio = self.portfolios[portfolio_id]
        
        # Get configuration
        if self.config_manager:
            confidence_threshold = self.config_manager.get_trading_config().get(
                'confidence_threshold', 0.70
            )
            sizing_config = self.config_manager.get_position_sizing_config()
            sizing_strategy = sizing_config.get('strategy', 'percentage')
            sizing_value = Decimal(str(sizing_config.get('value', 0.10)))
        else:
            # Use defaults
            confidence_threshold = 0.70
            sizing_strategy = 'percentage'
            sizing_value = Decimal("0.10")
        
        # Execute recommendation
        executor = TradeExecutor(portfolio, self.trade_history)
        return executor.execute_recommendation(
            recommendation,
            confidence_threshold,
            sizing_strategy,
            sizing_value
        )
    
    def get_performance_report(
        self,
        portfolio_id: str,
        current_prices: Optional[Dict[str, Decimal]] = None
    ) -> PerformanceReport:
        """
        Generates performance report for a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            current_prices: Optional dict mapping symbol to current price
            
        Returns:
            PerformanceReport object
            
        Raises:
            ValueError: If portfolio not found
        """
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        portfolio = self.portfolios[portfolio_id]
        calculator = PerformanceCalculator(portfolio, self.trade_history)
        
        return calculator.generate_performance_report(current_prices)
    
    def get_portfolio(self, portfolio_id: str) -> Portfolio:
        """
        Gets a portfolio by ID.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio object
            
        Raises:
            ValueError: If portfolio not found
        """
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        return self.portfolios[portfolio_id]
    def save_trade_history(self, filepath: str) -> None:
        """
        Saves trade history to file.

        Args:
            filepath: Path to save file
        """
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Save to file
        self.trade_history.save_to_file(filepath)

        self.logger.info(f"Saved trade history to {filepath}")

    def load_trade_history(self, filepath: str) -> None:
        """
        Loads trade history from file.

        Args:
            filepath: Path to load file
        """
        self.trade_history.load_from_file(filepath)

        self.logger.info(f"Loaded trade history from {filepath}")
