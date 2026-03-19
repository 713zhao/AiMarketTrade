"""
Brokers package for deerflow trading system.

This package handles broker API integration and live trading:
- adapters.py: BrokerAdapter abstract and implementations (Alpaca, Interactive Brokers)
- nodes.py: Trading execution nodes that use broker adapters
"""

# Re-export broker adapters
from .adapters import (
    BrokerAdapter,
    AlpacaAdapter,
    InteractiveBrokersAdapter,
)

# Re-export broker trading nodes
from .nodes import (
    BrokerConnectorNode,
    TradeExecutorNode,
    OrderMonitorNode,
    PositionManagerNode,
    AccountMonitorNode,
    RiskControlNode,
    ComplianceLoggerNode,
)

__all__ = [
    # Adapters
    "BrokerAdapter",
    "AlpacaAdapter",
    "InteractiveBrokersAdapter",
    # Trading Nodes
    "BrokerConnectorNode",
    "TradeExecutorNode",
    "OrderMonitorNode",
    "PositionManagerNode",
    "AccountMonitorNode",
    "RiskControlNode",
    "ComplianceLoggerNode",
]
