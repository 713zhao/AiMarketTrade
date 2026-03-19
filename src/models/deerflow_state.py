"""
Master DeerflowState - The central state object flowing through the graph.

This is the primary state schema used by LangGraph to maintain context
and pass data between nodes across all trading phases.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# Import from all model modules
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


class DeerflowState(BaseModel):
    """
    Master state object that flows through the entire deerflow graph.

    This is the primary state schema used by LangGraph to maintain
    context and pass data between nodes.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Session metadata
    session_id: str = Field("", description="Unique session identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Input parameters
    tickers: List[str] = Field(default_factory=list)
    analysis_scope: Dict[str, Any] = Field(default_factory=dict)

    # Data layer
    ticker_data: Dict[str, TickerData] = Field(default_factory=dict)

    # Analysis results per ticker
    technical_analyses: Dict[str, TechnicalAnalysis] = Field(default_factory=dict)
    fundamental_analyses: Dict[str, FundamentalAnalysis] = Field(default_factory=dict)
    news_analyses: Dict[str, NewsAnalysis] = Field(default_factory=dict)
    growth_analyses: Dict[str, GrowthAnalysis] = Field(default_factory=dict)
    macro_analyses: Dict[str, MacroAnalysis] = Field(default_factory=dict)
    risk_analyses: Dict[str, RiskAnalysis] = Field(default_factory=dict)
    consensus_signals: Dict[str, ConsensusSignal] = Field(default_factory=dict)

    # Final decisions
    trading_decisions: Dict[str, TradingDecision] = Field(default_factory=dict)
    
    # Phase 3: Portfolio-level analysis
    portfolio_risk_analysis: Optional[PortfolioRiskAnalysis] = Field(None, description="Portfolio-wide risk metrics")
    portfolio_optimization: Optional[PortfolioOptimizationResult] = Field(None, description="Optimized positions and allocation")
    monte_carlo_scenarios: List[ScenarioAnalysis] = Field(default_factory=list, description="MC simulation results")
    
    # Phase 4: Advanced optimization and macro integration
    macro_scenarios: List[MacroScenario] = Field(default_factory=list, description="Macroeconomic scenarios for analysis")
    multi_scenario_analysis: Optional[MultiScenarioAnalysis] = Field(None, description="Multi-scenario portfolio analysis")
    efficient_frontier: List[EfficientFrontierPoint] = Field(default_factory=list, description="Efficient frontier portfolios")
    market_regime: MarketRegime = Field(MarketRegime.SIDEWAYS, description="Current market regime classification")
    rebalancing_rules: List[RebalancingRule] = Field(default_factory=list, description="Rebalancing decisions")
    performance_attribution: Optional[PerformanceAttribution] = Field(None, description="Performance attribution analysis")
    
    # Phase 5: Production deployment & real-time integration
    efficient_frontier_data: Optional[EfficientFrontierData] = Field(None, description="Multiple frontier portfolios with constraints")
    transaction_execution_plan: Optional[TransactionExecutionPlan] = Field(None, description="Detailed execution plan with costs")
    backtest_result: Optional[BacktestResult] = Field(None, description="Historical strategy validation")
    portfolio_snapshot: Optional[PortfolioSnapshot] = Field(None, description="Real-time portfolio state")
    live_trading_session: Optional[LiveTradingSession] = Field(None, description="Active trading session tracking")
    performance_metrics: Optional[PerformanceMetricsSnapshot] = Field(None, description="Real-time performance metrics")

    # Phase 6: Broker API integration & live trading
    broker_accounts: Dict[str, BrokerAccount] = Field(default_factory=dict, description="Connected broker accounts")
    broker_connections: Dict[str, Any] = Field(default_factory=dict, description="Active broker API connections")
    broker_account_states: Dict[str, BrokerAccountState] = Field(default_factory=dict, description="Real-time broker account status")
    broker_execution_plan: Optional[BrokerExecutionPlan] = Field(None, description="Current execution plan with broker routing")
    submitted_orders: List[Order] = Field(default_factory=list, description="Orders submitted to brokers")
    pending_orders: List[Order] = Field(default_factory=list, description="Orders awaiting execution/fill")
    filled_trades: List[Trade] = Field(default_factory=list, description="Completed trades")
    compliance_records: List[ComplianceRecord] = Field(default_factory=list, description="Audit trail for compliance")
    last_validation: Optional[datetime] = Field(None, description="Last pre-trade validation")
    circuit_breaker_active: bool = Field(False, description="Risk circuit breaker triggered?")
    circuit_breaker_reason: str = Field("", description="Reason for circuit breaker halt")

    # Phase 7: Advanced Strategies & Derivatives Trading
    active_options: Dict[str, OptionContract] = Field(default_factory=dict, description="Active options positions")
    active_futures: Dict[str, FuturesContract] = Field(default_factory=dict, description="Active futures positions")
    active_crypto_derivatives: Dict[str, CryptoDerivative] = Field(default_factory=dict, description="Crypto perpetuals/futures")
    
    active_strategies: Dict[str, MultiLegOrder] = Field(default_factory=dict, description="Multi-leg strategy orders")
    strategy_performance: Dict[str, StrategyPerformance] = Field(default_factory=dict, description="Strategy P&L tracking")
    
    current_greeks: Dict[str, GreeksSnapshot] = Field(default_factory=dict, description="Greeks for all positions")
    greek_alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Greeks drift alerts")
    
    recommended_hedges: Dict[str, HedgeAllocation] = Field(default_factory=dict, description="Hedge recommendations")
    active_hedges: Dict[str, MultiLegOrder] = Field(default_factory=dict, description="Active hedging strategies")
    
    volatility_profiles: Dict[str, VolatilityProfile] = Field(default_factory=dict, description="Vol regimes by ticker")
    vol_opportunities: List[Dict[str, Any]] = Field(default_factory=list, description="Vol arbitrage opportunities")
    
    correlations: Dict[str, PairCorrelation] = Field(default_factory=dict, description="Pair correlations")
    active_pairs: Dict[str, PairCorrelation] = Field(default_factory=dict, description="Active pair trades")
    
    # Greeks management controls
    target_delta: float = Field(0.0, description="Portfolio-level delta target", ge=-1.0, le=1.0)
    rebalance_threshold: float = Field(0.15, description="Rebalance if delta drifts >15%", ge=0.0, le=1.0)
    last_greek_rebalance: Optional[datetime] = Field(None, description="Last Greeks rebalancing time")

    # ========================================================================
    # TRADING INTEGRATION: Virtual portfolio execution & tracking
    # ========================================================================
    trading_enabled: bool = Field(False, description="Enable virtual trading execution")
    portfolio_id: Optional[str] = Field(None, description="Virtual portfolio identifier")
    
    # Portfolio state
    cash_balance: float = Field(100000.0, description="Available cash in portfolio")
    positions: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Current holdings {ticker: {quantity, avg_cost, current_value}}"
    )
    
    # Trade execution
    pending_trades: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Trades awaiting execution from consensus"
    )
    executed_trades: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Historical executed trades with P&L"
    )
    
    # Portfolio metrics
    portfolio_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Aggregated P&L, returns, Sharpe, drawdown, win rate"
    )
    
    # Configuration
    trading_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Trading parameters: position_size_pct, slippage, commission, etc"
    )

    # Graph execution metadata
    active_nodes: List[str] = Field(default_factory=list)
    completed_nodes: List[str] = Field(default_factory=list)
    errors: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)

    # Cache and performance
    execution_time: Optional[float] = Field(None, description="Total execution time in seconds")
    cache_hits: int = Field(0, description="Number of cache hits")
    api_calls: int = Field(0, description="Number of API calls made")

    def get_analyst_results(self, ticker: str) -> Dict[str, Any]:
        """Get all analysis results for a specific ticker."""
        return {
            "technical": self.technical_analyses.get(ticker),
            "fundamental": self.fundamental_analyses.get(ticker),
            "news": self.news_analyses.get(ticker),
            "growth": self.growth_analyses.get(ticker),
            "macro": self.macro_analyses.get(ticker),
            "risk": self.risk_analyses.get(ticker),
            "consensus": self.consensus_signals.get(ticker),
            "decision": self.trading_decisions.get(ticker),
        }

    def has_complete_analysis(self, ticker: str) -> bool:
        """Check if all core analyses are complete for a ticker."""
        required = [
            self.technical_analyses.get(ticker),
            self.fundamental_analyses.get(ticker),
            self.news_analyses.get(ticker),
            self.risk_analyses.get(ticker),
        ]
        return all(required)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    def add_error(self, node: str, error: str, ticker: Optional[str] = None) -> None:
        """Log an error for a specific node and optional ticker."""
        error_entry = {
            "node": node,
            "error": error,
            "ticker": ticker,
            "timestamp": datetime.utcnow(),
        }
        if node not in self.errors:
            self.errors[node] = []
        self.errors[node].append(error_entry)


__all__ = [
    "DeerflowState",
    # Re-export all enums and models for convenience
    "AnalystType",
    "SignalType",
    "DataProvider",
    "MarketRegime",
    "TickerData",
    "TechnicalAnalysis",
    "FundamentalAnalysis",
    "NewsAnalysis",
    "GrowthAnalysis",
    "RiskAnalysis",
    "MacroAnalysis",
    "ConsensusSignal",
    "TradingDecision",
    "ScenarioAnalysis",
    "PortfolioRiskAnalysis",
    "PortfolioOptimizationResult",
    "MacroScenario",
    "RebalancingRule",
    "MultiScenarioAnalysis",
    "BacktestPeriod",
    "BacktestResult",
    "EfficientFrontierPoint",
    "EfficientFrontierData",
    "TransactionExecutionPlan",
    "PortfolioSnapshot",
    "LiveTradingSession",
    "PerformanceMetricsSnapshot",
    "TransactionCostAnalysis",
    "PerformanceAttribution",
    "BrokerAccount",
    "Order",
    "BrokerPosition",
    "Trade",
    "BrokerAccountState",
    "BrokerExecutionPlan",
    "ComplianceRecord",
    "OptionContract",
    "FuturesContract",
    "CryptoDerivative",
    "MultiLegOrder",
    "GreeksSnapshot",
    "HedgeAllocation",
    "StrategyPerformance",
    "VolatilityProfile",
    "PairCorrelation",
]
