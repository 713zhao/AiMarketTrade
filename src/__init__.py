"""
Deerflow + OpenBB Trading System

A production-ready multi-agent trading system combining deerflow's
LangGraph-based orchestration with OpenBB's comprehensive financial data.

Phase 1: Foundation
- Core infrastructure setup
- Data access validation (OpenBB SDK)
- State schema for multi-agent communication
- Basic pipeline: Data → Technical Analysis → Decision
"""

__version__ = "0.1.0"
__author__ = "OpenClaw"
__email__ = "user@example.com"

from .config import get_settings, reload_settings, Settings
from .models import (
    DeerflowState,
    TickerData,
    TechnicalAnalysis,
    FundamentalAnalysis,
    NewsAnalysis,
    GrowthAnalysis,
    RiskAnalysis,
    MacroAnalysis,
    ConsensusSignal,
    TradingDecision,
    AnalystType,
    SignalType,
    DataProvider,
)
from .nodes import StockDataNode, TechnicalAnalystNode, DecisionNode, BaseNode
from .graph import (
    create_deerflow_graph,
    run_deerflow_graph,
    print_state_summary,
    create_mock_graph,
)

__all__ = [
    # Config
    "get_settings",
    "reload_settings",
    "Settings",

    # State
    "DeerflowState",
    "TickerData",
    "TechnicalAnalysis",
    "FundamentalAnalysis",
    "NewsAnalysis",
    "GrowthAnalysis",
    "RiskAnalysis",
    "MacroAnalysis",
    "ConsensusSignal",
    "TradingDecision",
    "AnalystType",
    "SignalType",
    "DataProvider",

    # Nodes
    "BaseNode",
    "StockDataNode",
    "TechnicalAnalystNode",
    "DecisionNode",

    # Graph
    "create_deerflow_graph",
    "run_deerflow_graph",
    "print_state_summary",
    "create_mock_graph",
]
