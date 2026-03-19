"""
Backtest result data model for trading simulation.
"""

import json
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from .performance_report import PerformanceReport


@dataclass
class BacktestResult:
    """
    Results from a backtest simulation.
    
    Attributes:
        backtest_id: Unique identifier for the backtest
        start_date: Start date of backtest period
        end_date: End date of backtest period
        initial_cash: Starting cash balance
        final_portfolio_value: Final portfolio value
        performance_report: Detailed performance metrics
        total_recommendations_processed: Number of recommendations processed
    """
    
    backtest_id: str
    start_date: datetime
    end_date: datetime
    initial_cash: Decimal
    final_portfolio_value: Decimal
    performance_report: PerformanceReport
    total_recommendations_processed: int
    
    def to_dict(self) -> dict:
        """
        Serializes backtest result to dictionary format.
        
        Returns:
            Dictionary representation
        """
        return {
            'backtest_id': self.backtest_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_cash': str(self.initial_cash),
            'final_portfolio_value': str(self.final_portfolio_value),
            'total_recommendations_processed': self.total_recommendations_processed,
            'performance_report': json.loads(self.performance_report.to_json())
        }
    
    def to_json(self) -> str:
        """
        Serializes backtest result to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)
