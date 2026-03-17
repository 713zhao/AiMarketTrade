"""
Node modules for the DeerFlow trading system.

This package organizes all trading logic nodes into focused modules:
- base: Abstract base node class
- data_node: Market data fetching
- analyst_nodes: Technical, fundamental, news, growth, and risk analysis
- consensus_node: Signal aggregation and decision making
- portfolio_nodes: Portfolio-level analysis and optimization
- production_nodes: Efficient frontier, attribution, costs, backtesting
"""

# Base node interface
from .base import BaseNode, NodeResult

# Data node
from .data_node import StockDataNode

# Analyst nodes
from .analyst_nodes import (
    TechnicalAnalystNode,
    NewsAnalystNode,
    FundamentalsAnalystNode,
    GrowthAnalystNode,
    RiskAnalystNode,
    MacroAnalystNode,
)

# Consensus and decision nodes
from .consensus_node import ConsensusNode, DecisionNode

# Portfolio nodes
from .portfolio_nodes import (
    PortfolioRiskNode,
    PortfolioOptimizationNode,
    MacroScenarioNode,
    MultiScenarioAnalysisNode,
    RebalancingNode,
)

# Production nodes
from .production_nodes import (
    EfficientFrontierNode,
    PerformanceAttributionNode,
    TransactionCostNode,
    BacktestingEngineNode,
)

__all__ = [
    # Base
    "BaseNode",
    "NodeResult",
    # Data
    "StockDataNode",
    # Analysts
    "TechnicalAnalystNode",
    "NewsAnalystNode",
    "FundamentalsAnalystNode",
    "GrowthAnalystNode",
    "RiskAnalystNode",
    "MacroAnalystNode",
    # Consensus
    "ConsensusNode",
    "DecisionNode",
    # Portfolio
    "PortfolioRiskNode",
    "PortfolioOptimizationNode",
    "MacroScenarioNode",
    "MultiScenarioAnalysisNode",
    "RebalancingNode",
    # Production
    "EfficientFrontierNode",
    "PerformanceAttributionNode",
    "TransactionCostNode",
    "BacktestingEngineNode",
]
