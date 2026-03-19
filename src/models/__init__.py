"""
Models package for the deerflow trading system.

This package organizes all trading system models by phase:
- base: Core enumerations and types
- ticker_models: Phase 1-2 ticker data and analysis models
- analysis_models: Phase 2-3 consensus and decision models
- portfolio_models: Phase 3-4 portfolio and optimization models
- production_models: Phase 5 backtesting and production models
- broker_models: Phase 6 broker API integration models
- advanced_models: Phase 7 advanced strategies and derivatives models
- deerflow_state: Master state object
"""

# Import from modularized structure
from .base import (
    AnalystType,
    SignalType,
    DataProvider,
    MarketRegime,
)
from .ticker_models import (
    TickerData,
    TechnicalAnalysis,
    FundamentalAnalysis,
    NewsAnalysis,
)
from .analysis_models import (
    GrowthAnalysis,
    RiskAnalysis,
    MacroAnalysis,
    ConsensusSignal,
    TradingDecision,
    ScenarioAnalysis,
)
from .portfolio_models import (
    PortfolioRiskAnalysis,
    PortfolioOptimizationResult,
    MacroScenario,
    RebalancingRule,
    MultiScenarioAnalysis,
)
from .production_models import (
    BacktestPeriod,
    BacktestResult,
    EfficientFrontierPoint,
    EfficientFrontierData,
    TransactionExecutionPlan,
    PortfolioSnapshot,
    LiveTradingSession,
    PerformanceMetricsSnapshot,
    TransactionCostAnalysis,
    PerformanceAttribution,
)
from .broker_models import (
    BrokerAccount,
    Order,
    BrokerPosition,
    Trade,
    BrokerAccountState,
    BrokerExecutionPlan,
    ComplianceRecord,
)
from .advanced_models import (
    OptionContract,
    FuturesContract,
    CryptoDerivative,
    MultiLegOrder,
    GreeksSnapshot,
    HedgeAllocation,
    StrategyPerformance,
    VolatilityProfile,
    PairCorrelation,
)
from .trading_models import (
    TradeAction,
    ExecutedTrade,
    PortfolioPosition,
    PortfolioMetrics,
    TradingSession,
    TradeRecommendation,
    PortfolioStats,
    PositionDriftAnalysis,
    VirtualExecutionRecord,
)
from .deerflow_state import DeerflowState

# Import get_settings from config
try:
    from ..config import get_settings
except ImportError:
    from config import get_settings

__all__ = [
    # Base types
    "AnalystType",
    "SignalType",
    "DataProvider",
    "MarketRegime",
    # Phase 1-2 models
    "TickerData",
    "TechnicalAnalysis",
    "FundamentalAnalysis",
    "NewsAnalysis",
    "GrowthAnalysis",
    "RiskAnalysis",
    "MacroAnalysis",
    # Phase 2-3 models
    "ConsensusSignal",
    "TradingDecision",
    "ScenarioAnalysis",
    # Phase 3-4 models
    "PortfolioRiskAnalysis",
    "PortfolioOptimizationResult",
    "MacroScenario",
    "RebalancingRule",
    "PerformanceAttribution",
    "EfficientFrontierPoint",
    "MultiScenarioAnalysis",
    # Phase 5 models
    "BacktestPeriod",
    "BacktestResult",
    "EfficientFrontierData",
    "TransactionExecutionPlan",
    "PortfolioSnapshot",
    "LiveTradingSession",
    "PerformanceMetricsSnapshot",
    "TransactionCostAnalysis",
    # Phase 6 models
    "BrokerAccount",
    "Order",
    "BrokerPosition",
    "Trade",
    "BrokerAccountState",
    "BrokerExecutionPlan",
    "ComplianceRecord",
    # Phase 7 models
    "OptionContract",
    "FuturesContract",
    "CryptoDerivative",
    "MultiLegOrder",
    "GreeksSnapshot",
    "HedgeAllocation",
    "StrategyPerformance",
    "VolatilityProfile",
    "PairCorrelation",
    # Trading integration models
    "TradeAction",
    "ExecutedTrade",
    "PortfolioPosition",
    "PortfolioMetrics",
    "TradingSession",
    "TradeRecommendation",
    "PortfolioStats",
    "PositionDriftAnalysis",
    "VirtualExecutionRecord",
    # Master state
    "DeerflowState",
    # Utilities
    "get_settings",
]
