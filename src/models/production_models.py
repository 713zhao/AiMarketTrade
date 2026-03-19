"""
Production deployment and real-time models (Phase 5).

Backtesting results, execution plans, portfolio snapshots, and live trading state.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BacktestPeriod(BaseModel):
    """Historical backtest period results."""
    period_id: int = Field(description="Period identifier")
    start_date: datetime = Field(description="Period start date")
    end_date: datetime = Field(description="Period end date")
    portfolio_return: float = Field(0.0, description="Portfolio return in period")
    benchmark_return: float = Field(0.0, description="Benchmark return")
    outperformance: float = Field(0.0, description="Active return vs benchmark")
    volatility: float = Field(0.0, description="Period volatility")
    max_drawdown: float = Field(0.0, description="Maximum drawdown in period")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio")
    num_trades: int = Field(0, description="Number of trades executed")
    total_costs: float = Field(0.0, description="Total transaction costs")
    turnover: float = Field(0.0, description="Portfolio turnover")


class BacktestResult(BaseModel):
    """Complete backtest validation of trading strategy."""
    backtest_id: str = Field(description="Unique backtest identifier")
    backtest_name: str = Field(description="Descriptive name")
    backtest_start_date: datetime = Field(description="Backtest period start")
    backtest_end_date: datetime = Field(description="Backtest period end")
    backtest_period_days: int = Field(0, description="Number of trading days")
    backtest_days: int = Field(0, description="Number of trading days (alias)")
    initial_capital: float = Field(1000000, description="Starting capital")
    final_portfolio_value: float = Field(0.0, description="Ending portfolio value")
    total_return: float = Field(0.0, description="Cumulative total return")
    annualized_return: float = Field(0.0, description="Annualized return (%)")
    volatility: float = Field(0.0, description="Annualized volatility (%)")
    annualized_volatility: float = Field(0.0, description="Annualized volatility (alias)")
    sharpe_ratio: float = Field(0.0, description="Overall Sharpe ratio")
    sortino_ratio: float = Field(0.0, description="Downside risk adjusted")
    max_drawdown: float = Field(0.0, description="Maximum drawdown (%)")
    maximum_drawdown: float = Field(0.0, description="Max DD during backtest")
    winning_trades: int = Field(0, description="Number of winning trades")
    losing_trades: int = Field(0, description="Number of losing trades")
    win_rate: float = Field(0.0, description="Win rate")
    profit_factor: float = Field(0.0, description="Profit / loss")
    trades_executed: int = Field(0, description="Total transaction count")
    total_transaction_costs: float = Field(0.0, description="Total transaction costs")
    best_day: float = Field(0.0, description="Best daily return")
    worst_day: float = Field(0.0, description="Worst daily return")
    recovery_time_days: int = Field(0, description="Average recovery time")
    final_commentary: str = Field("", description="Backtest summary")
    summary: str = Field("", description="Backtest results summary")
    conclusion: str = Field("", description="Backtest conclusion and recommendations")
    
    # Additional metrics
    benchmark_return: float = Field(0.0, description="Benchmark return for comparison")
    information_ratio: float = Field(0.0, description="Information ratio vs benchmark")
    periods: List[Dict[str, Any]] = Field(default_factory=list, description="Period-by-period returns")
    total_months: int = Field(0, description="Number of months in backtest")
    positive_months: int = Field(0, description="Number of positive months")
    slippage_per_trade: float = Field(0.0, description="Average slippage per trade")


class EfficientFrontierPoint(BaseModel):
    """
    Point on the efficient frontier: portfolio with optimal risk/return.
    """
    portfolio_id: int = Field(description="Portfolio identifier on frontier")
    expected_return: float = Field(0.0, description="Expected annual return")
    volatility: float = Field(0.15, description="Expected volatility (annualized)")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio")
    
    # Allocation
    portfolio_weights: Dict[str, float] = Field(default_factory=dict, description="Ticker weights")
    
    # Risk metrics
    risk_adjusted_return: float = Field(0.0, description="Return/volatility ratio")
    herfindahl_index: float = Field(0.0, description="Concentration metric")
    effective_assets: float = Field(0.0, description="Effective number of assets")


class EfficientFrontierData(BaseModel):
    """Multiple portfolios spanning the efficient frontier."""
    num_portfolios: int = Field(50, description="Number of portfolios on frontier")
    min_return: float = Field(0.0, description="Minimum return on frontier")
    max_return: float = Field(0.20, description="Maximum return on frontier")
    portfolios: List[EfficientFrontierPoint] = Field(default_factory=list, description="Frontier portfolios")
    global_minimum_variance: Optional[EfficientFrontierPoint] = Field(None, description="Lowest risk")
    maximum_sharpe_portfolio: Optional[EfficientFrontierPoint] = Field(None, description="Best risk-adjusted")
    current_portfolio: Optional[EfficientFrontierPoint] = Field(None, description="Current allocation")
    constraints_active: List[str] = Field(default_factory=list, description="Active constraints")
    constraint_impacts: Dict[str, float] = Field(default_factory=dict, description="Impact of constraints")
    summary: str = Field("", description="Frontier analysis summary")


class TransactionExecutionPlan(BaseModel):
    """Detailed execution plan with transaction costs."""
    execution_id: str = Field(description="Unique execution identifier")
    execution_date: datetime = Field(default_factory=datetime.utcnow)
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="Individual trades")
    estimated_commission: float = Field(0.0, description="Estimated commission")
    estimated_market_impact: float = Field(0.0, description="Estimated market impact")
    estimated_slippage: float = Field(0.0, description="Estimated slippage")
    estimated_opportunity_cost: float = Field(0.0, description="Cost of delayed execution")
    total_estimated_cost: float = Field(0.0, description="Total costs")
    total_cost_bps: float = Field(0.0, description="Costs in basis points")
    execution_strategy: str = Field("vwap", description="Execution algorithm")
    execution_timeline: str = Field("1 day", description="Execution speed")
    max_order_size: float = Field(0.2, description="Max order size as % of daily volume")
    avoid_news: bool = Field(False, description="Avoid news events")
    tax_aware: bool = Field(False, description="Tax-aware execution")
    market_hours_only: bool = Field(False, description="Execute during market hours only")
    summary: str = Field("", description="Execution plan summary")


class PortfolioSnapshot(BaseModel):
    """Real-time portfolio state and metrics snapshot."""
    snapshot_id: str = Field(description="Unique snapshot identifier")
    snapshot_time: datetime = Field(default_factory=datetime.utcnow)
    current_positions: Dict[str, float] = Field(default_factory=dict, description="Current holdings")
    target_positions: Dict[str, float] = Field(default_factory=dict, description="Target allocations")
    position_drift: Dict[str, float] = Field(default_factory=dict, description="Drift from target positions")
    total_value: float = Field(0.0, description="Total portfolio value")
    cash_position: float = Field(0.0, description="Cash & equivalents")
    portfolio_volatility: float = Field(0.0, description="Current volatility")
    portfolio_beta: float = Field(1.0, description="Market beta")
    portfolio_drawdown: float = Field(0.0, description="Current drawdown")
    ytd_return: float = Field(0.0, description="Year-to-date return")
    rebalancing_needed: bool = Field(False, description="Rebalancing triggered?")


class LiveTradingSession(BaseModel):
    """Real-time active trading session state."""
    session_id: str = Field(description="Unique session identifier")
    session_start: datetime = Field(description="Session start time")
    session_end: Optional[datetime] = Field(None, description="Session end time")
    starting_portfolio: Dict[str, float] = Field(default_factory=dict)
    current_portfolio: Dict[str, float] = Field(default_factory=dict)
    starting_value: float = Field(0.0, description="Starting value")
    current_value: float = Field(0.0, description="Current value")
    session_pnl: float = Field(0.0, description="Session PnL")
    session_pnl_pct: float = Field(0.0, description="Session return %")
    trades_executed: List[Dict[str, Any]] = Field(default_factory=list, description="Executed trades")
    total_commissions: float = Field(0.0, description="Total commissions")
    is_active: bool = Field(True, description="Is session active?")


class PerformanceMetricsSnapshot(BaseModel):
    """Comprehensive real-time performance metrics snapshot."""
    metrics_date: datetime = Field(default_factory=datetime.utcnow)
    daily_return: float = Field(0.0, description="Daily return")
    weekly_return: float = Field(0.0, description="Weekly return")
    monthly_return: float = Field(0.0, description="Monthly return")
    ytd_return: float = Field(0.0, description="Year-to-date return")
    inception_return: float = Field(0.0, description="Inception return")
    daily_volatility: float = Field(0.0, description="Daily volatility")
    rolling_volatility_20d: float = Field(0.0, description="20-day rolling volatility")
    rolling_volatility_60d: float = Field(0.0, description="60-day rolling volatility")
    current_drawdown: float = Field(0.0, description="Current drawdown")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio")
    sharpe_ratio_annual: float = Field(0.0, description="Annualized Sharpe ratio")
    sortino_ratio: float = Field(0.0, description="Sortino ratio")
    positive_days: int = Field(0, description="Positive days")
    total_days: int = Field(0, description="Total days")
    win_rate: float = Field(0.0, description="Win rate %")
    best_day: float = Field(0.0, description="Best daily return")
    worst_day: float = Field(0.0, description="Worst daily return")


class TransactionCostAnalysis(BaseModel):
    """Analysis of transaction costs."""
    transaction_type: str = Field("rebalancing", description="Type of transaction")
    estimated_total_cost: float = Field(0.0, description="Total cost")
    percentage_of_portfolio: float = Field(0.0, description="Cost as % of portfolio")
    commission_cost: float = Field(0.0, description="Commission cost")
    bid_ask_spread_cost: float = Field(0.0, description="Bid-ask spread cost")
    market_impact_cost: float = Field(0.0, description="Market impact cost")
    number_of_trades: int = Field(0, description="Number of trades")
    cost_breakdown: Dict[str, float] = Field(default_factory=dict, description="Cost by ticker")
    cost_minimization_strategies: List[str] = Field(default_factory=list, description="Strategies")
    net_benefit_analysis: str = Field("", description="Benefit analysis")
    confidence: float = Field(0.75, description="Confidence level")


class PerformanceAttribution(BaseModel):
    """
    Attribution analysis: what drove returns?
    
    Decomposes portfolio performance into:
    - Allocation effect: Due to tactical allocation decisions
    - Selection effect: Due to picking best performers
    - Interaction effect: Combined effect
    """
    ticker: str = Field(description="Ticker symbol")
    period_return: float = Field(0.0, description="Total return in period")
    technical_contribution: float = Field(0.0, description="Return from technical factors")
    fundamental_contribution: float = Field(0.0, description="Return from fundamental factors")
    sentiment_contribution: float = Field(0.0, description="Return from sentiment/news")
    macro_contribution: float = Field(0.0, description="Return from macro factors")
    idiosyncratic_return: float = Field(0.0, description="Unexplained return")
    signal_accuracy: float = Field(0.55, description="Accuracy  of trading signals")
    timing_effectiveness: float = Field(0.5, description="Effectiveness of trade timing")
    
    # Attribution decomposition
    allocation_effect: float = Field(0.0, description="Return from allocation decisions")
    selection_effect: float = Field(0.0, description="Return from security selection")
    interaction_effect: float = Field(0.0, description="Combined allocation and selection effect")
    portfolio_return: float = Field(0.0, description="Total portfolio return")
    
    # Top contributors and detractors
    top_contributors: List[tuple] = Field(default_factory=list, description="Top contributing holdings")
    top_detractors: List[tuple] = Field(default_factory=list, description="Top detracting holdings")
    
    # Holding-level attribution
    holding_attribution: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Per-holding attribution analysis")


__all__ = [
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
]
