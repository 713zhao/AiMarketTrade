"""
Backtest Engine component for trading simulation.
"""

import logging
import uuid
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from .models.portfolio import Portfolio
from .models.trade_history import TradeHistory
from .models.backtest_result import BacktestResult
from .trade_executor import TradeExecutor
from .performance_calculator import PerformanceCalculator


class BacktestEngine:
    """
    Executes backtests on historical recommendations.
    
    Responsibilities:
    - Run backtests with historical data
    - Process recommendations chronologically
    - Maintain isolated backtest portfolio
    - Generate backtest results and performance reports
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize Backtest Engine.
        
        Args:
            config_manager: Optional ConfigurationManager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Backtest Engine initialized")
    
    def run_backtest(
        self,
        recommendations: List,
        initial_cash: Optional[Decimal] = None,
        confidence_threshold: Optional[float] = None
    ) -> BacktestResult:
        """
        Runs a backtest on historical recommendations.
        
        Args:
            recommendations: List of StockRecommendation objects with timestamps
            initial_cash: Optional initial cash balance (uses config default if None)
            confidence_threshold: Optional confidence threshold (uses config default if None)
            
        Returns:
            BacktestResult object with performance metrics
        """
        # Get configuration
        if initial_cash is None:
            if self.config_manager:
                initial_cash = Decimal(str(
                    self.config_manager.get_trading_config().get('initial_cash_balance', 100000.00)
                ))
            else:
                initial_cash = Decimal("100000.00")
        
        if confidence_threshold is None:
            if self.config_manager:
                confidence_threshold = self.config_manager.get_trading_config().get(
                    'confidence_threshold', 0.70
                )
            else:
                confidence_threshold = 0.70
        
        # Get position sizing configuration
        if self.config_manager:
            sizing_config = self.config_manager.get_position_sizing_config()
            sizing_strategy = sizing_config.get('strategy', 'percentage')
            sizing_value = Decimal(str(sizing_config.get('value', 0.10)))
        else:
            sizing_strategy = 'percentage'
            sizing_value = Decimal("0.10")
        
        # Sort recommendations chronologically
        sorted_recommendations = sorted(recommendations, key=lambda r: r.generated_at)
        
        if not sorted_recommendations:
            self.logger.warning("No recommendations provided for backtest")
            # Return empty backtest result
            backtest_id = str(uuid.uuid4())
            portfolio = Portfolio(
                portfolio_id=str(uuid.uuid4()),
                cash_balance=initial_cash,
                initial_cash_balance=initial_cash
            )
            trade_history = TradeHistory(storage_path=f"data/backtest_{backtest_id}_history.json")
            calculator = PerformanceCalculator(portfolio, trade_history)
            performance_report = calculator.generate_performance_report()
            
            return BacktestResult(
                backtest_id=backtest_id,
                start_date=datetime.now(),
                end_date=datetime.now(),
                initial_cash=initial_cash,
                final_portfolio_value=initial_cash,
                performance_report=performance_report,
                total_recommendations_processed=0
            )
        
        # Create backtest portfolio
        backtest_id = str(uuid.uuid4())
        portfolio = Portfolio(
            portfolio_id=str(uuid.uuid4()),
            cash_balance=initial_cash,
            initial_cash_balance=initial_cash
        )
        
        # Create separate trade history for backtest
        trade_history = TradeHistory(storage_path=f"data/backtest_{backtest_id}_history.json")
        
        # Create executor
        executor = TradeExecutor(portfolio, trade_history)
        
        # Track dates
        start_date = sorted_recommendations[0].generated_at
        end_date = sorted_recommendations[-1].generated_at
        
        # Process each recommendation
        trades_executed = 0
        for recommendation in sorted_recommendations:
            trade = executor.execute_recommendation(
                recommendation,
                confidence_threshold,
                sizing_strategy,
                sizing_value
            )
            if trade:
                trades_executed += 1
        
        self.logger.info(
            f"Backtest complete: processed {len(sorted_recommendations)} recommendations, "
            f"executed {trades_executed} trades"
        )
        
        # Generate performance report
        calculator = PerformanceCalculator(portfolio, trade_history)
        performance_report = calculator.generate_performance_report()
        
        # Calculate final portfolio value
        final_value = calculator.calculate_portfolio_value()
        
        # Create backtest result
        result = BacktestResult(
            backtest_id=backtest_id,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            final_portfolio_value=final_value,
            performance_report=performance_report,
            total_recommendations_processed=len(sorted_recommendations)
        )
        
        return result
