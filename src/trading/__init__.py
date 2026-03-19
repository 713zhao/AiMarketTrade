"""
Trading Simulation System

This module provides virtual trading capabilities to test trading strategies
with simulated money based on AnalysisEngine recommendations.
"""

from .models.portfolio import Portfolio
from .models.position import Position
from .models.trade import Trade
from .models.trade_history import TradeHistory
from .models.performance_report import PerformanceReport
from .models.backtest_result import BacktestResult
from .trade_executor import TradeExecutor
from .performance_calculator import PerformanceCalculator
from .trading_simulator import TradingSimulator
from .backtest_engine import BacktestEngine
from .integration import TradingIntegration

__all__ = [
    'Portfolio',
    'Position',
    'Trade',
    'TradeHistory',
    'PerformanceReport',
    'BacktestResult',
    'TradeExecutor',
    'PerformanceCalculator',
    'TradingSimulator',
    'BacktestEngine',
    'TradingIntegration',
]
