"""
Advanced strategies and derivatives trading models (Phase 7).

Complex trading strategies including options, futures, crypto derivatives,
and greeks-based hedging.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OptionContract(BaseModel):
    """
    Details for equity/index options contracts.
    
    期权合约细节，包括Greeks和定价数据。
    """
    contract_id: str = Field(description="Unique contract ID")
    ticker: str = Field(description="Underlying symbol")
    contract_type: str = Field(description="CALL or PUT")
    expiration: datetime = Field(description="Expiration date")
    strike: float = Field(description="Strike price", ge=0.0)
    
    # Pricing
    bid: float = Field(0.0, description="Current bid price")
    ask: float = Field(0.0, description="Current ask price")
    last: float = Field(0.0, description="Last trade price")
    volume: int = Field(0, description="Daily volume")
    open_interest: int = Field(0, description="Total open contracts")
    
    # Greeks
    implied_volatility: float = Field(0.25, description="IV as decimal (0.25 = 25%)", ge=0.0, le=3.0)
    delta: float = Field(0.0, description="Delta (directional sensitivity)", ge=-1.0, le=1.0)
    gamma: float = Field(0.0, description="Gamma (curvature)")
    theta: float = Field(0.0, description="Theta (daily decay in $)")
    vega: float = Field(0.0, description="Vega (IV sensitivity in $)")
    rho: float = Field(0.0, description="Rho (interest rate sensitivity)")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_tradeable: bool = Field(True, description="Is option currently tradeable")


class FuturesContract(BaseModel):
    """
    Futures contract specifications and quotes.
    
    期货合约规格和报价。
    """
    contract_id: str = Field(description="Unique contract ID")
    symbol: str = Field(description="Futures symbol (ES, NQ, YM, GC, CL, etc)")
    contract_code: str = Field(description="Full code (ESH24 = Mar 2024 E-mini S&P)")
    expiration: datetime = Field(description="Last trading day")
    multiplier: float = Field(50.0, description="Contract multiplier", gt=0.0)
    
    # Pricing
    bid: float = Field(0.0, description="Current bid")
    ask: float = Field(0.0, description="Current ask")
    current_price: float = Field(0.0, description="Current mark price")
    settlement_price: float = Field(0.0, description="Previous settlement")
    
    # Movement
    daily_change: float = Field(0.0, description="Change today")
    daily_change_pct: float = Field(0.0, description="% change today")
    volume: int = Field(0, description="Daily volume")
    open_interest: int = Field(0, description="Total open contracts")
    bid_volume: int = Field(0, description="Bid size")
    ask_volume: int = Field(0, description="Ask size")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    contract_type: str = Field("INDEX", description="INDEX, COMMODITY, FOREX, CRYPTO")
    exchange: str = Field("CME", description="CME, ICE, CBOE, etc")


class CryptoDerivative(BaseModel):
    """
    Cryptocurrency futures and perpetuals.
    
    加密货币期货和永续合约。
    """
    contract_id: str = Field(description="Unique ID")
    underlying: str = Field(description="BTC, ETH, SOL, etc")
    contract_type: str = Field(description="PERPETUAL or FUTURES")
    expiration: Optional[datetime] = Field(None, description="Null for perpetuals")
    
    # Pricing
    bid: float = Field(0.0, description="Current bid")
    ask: float = Field(0.0, description="Current ask")
    index_price: float = Field(0.0, description="Underlying spot price")
    mark_price: float = Field(0.0, description="Mark price (perps have basis)")
    
    # Perpetual specific
    funding_rate: float = Field(0.0, description="Hourly funding rate")
    funding_rate_8h: float = Field(0.0, description="Predicted 8-hour rate")
    
    # Volumes and interest
    bid_volume: float = Field(0.0, description="Bid volume in contracts")
    ask_volume: float = Field(0.0, description="Ask volume in contracts")
    volume_24h: float = Field(0.0, description="Volume in USD")
    open_interest: float = Field(0.0, description="Total open contracts")
    
    # Liquidation
    liquidation_price_long: float = Field(0.0, description="Long liquidation level")
    liquidation_price_short: float = Field(0.0, description="Short liquidation level")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    exchange: str = Field("Binance", description="Binance, FTX, Bybit, Deribit, etc")


class MultiLegOrder(BaseModel):
    """
    Coordinated multi-leg strategy execution.
    
    多腿策略的协调执行。
    """
    strategy_id: str = Field(description="Unique strategy ID")
    strategy_name: str = Field(description="CALL_SPREAD, IRON_CONDOR, PAIR_TRADE, etc")
    
    # Legs (each contains multiple fields)
    legs: List[Dict[str, Any]] = Field(default_factory=list, description="Each leg with order details")
    
    # Strategy economics
    total_cost: float = Field(0.0, description="Net debit/credit for entire strategy")
    max_loss: float = Field(0.0, description="Max loss if all legs filled at limit")
    max_profit: float = Field(0.0, description="Max profit on strategy")
    breakeven: List[float] = Field(default_factory=list, description="Breakeven price(s)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = Field(None)
    status: str = Field("PLANNED", description="PLANNED, EXECUTING, FILLED, PARTIAL, CANCELLED")
    execution_order: List[int] = Field(default_factory=list, description="Order to execute legs")
    notes: str = Field("", description="Strategy thesis and exit plan")


class GreeksSnapshot(BaseModel):
    """
    Real-time Greeks for position monitoring.
    
    实时希腊字母（Greeks）用于头寸监控。
    """
    snapshot_id: str = Field(description="Unique snapshot ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    position_id: str = Field(description="Which position/strategy")
    
    # Aggregate Greeks
    total_delta: float = Field(0.0, description="Share equivalents")
    total_gamma: float = Field(0.0, description="Delta change per 1% move")
    total_theta: float = Field(0.0, description="Daily decay in USD")
    total_vega: float = Field(0.0, description="Per 1% IV change")
    total_rho: float = Field(0.0, description="Per 1% rate change")
    
    # By leg
    leg_greeks: List[Dict[str, float]] = Field(default_factory=list, description="Greeks for each leg")
    
    # Risk metrics
    delta_pct: float = Field(0.0, description="% of portfolio at risk")
    theta_as_return_pct: float = Field(0.0, description="Theta as % return")
    vega_exposure: float = Field(0.0, description="IV sensitivity in $")
    gamma_exposure: float = Field(0.0, description="Convexity in $")
    
    # Alerts
    delta_drift_alert: bool = Field(False, description="Delta drifted >10%?")
    theta_decay_strong: bool = Field(False, description="High time decay?")
    gamma_risk_high: bool = Field(False, description="High gamma near expiration?")
    vega_exposure_alert: bool = Field(False, description="High IV sensitivity?")
    
    rebalance_needed: bool = Field(False, description="Should rebalance?")
    rebalance_shares: Optional[int] = Field(None, description="How many shares to hedge")
    rebalance_cost: Optional[float] = Field(None, description="Rebalance cost")


class HedgeAllocation(BaseModel):
    """
    Recommended hedging position sizing.
    
    推荐对冲头寸规模。
    """
    allocation_id: str = Field(description="Unique allocation ID")
    base_position: Dict[str, Any] = Field(default_factory=dict, description="Position being hedged")
    
    # Strategies (ranked by efficiency)
    hedging_strategies: List[Dict[str, Any]] = Field(default_factory=list, description="Strategy options")
    
    optimal_hedge: str = Field("", description="Recommended strategy")
    hedge_ratio: float = Field(1.0, description="% of position to hedge", ge=0.0, le=1.0)
    cost_as_pct_position: float = Field(0.0, description="Cost as % of value")
    protection_level: float = Field(0.0, description="Downside protected to this price")
    
    # Details
    thesis: str = Field("", description="Why this hedge")
    conditions_to_close: List[str] = Field(default_factory=list, description="When to close")
    max_duration_days: int = Field(60, description="Max hold period")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=datetime.utcnow, description="Recommendation expiration")


class StrategyPerformance(BaseModel):
    """
    Track performance of multi-leg strategies.
    
    跟踪多腿策略的性能。
    """
    performance_id: str = Field(description="Unique ID")
    strategy_id: str = Field(description="Which strategy")
    strategy_name: str = Field(description="Strategy name")
    
    # Entry
    entry_price: float = Field(0.0, description="Entry mark price")
    entry_date: datetime = Field(default_factory=datetime.utcnow)
    entry_capital: float = Field(0.0, description="Capital deployed")
    
    # Current
    current_price: float = Field(0.0, description="Current mark")
    days_held: int = Field(0, description="Days held")
    
    # P&L
    theoretical_pnl: float = Field(0.0, description="If closed at current prices")
    theta_accumulated: float = Field(0.0, description="Time decay captured")
    gamma_pnl: float = Field(0.0, description="Realized gamma P&L")
    vega_pnl: float = Field(0.0, description="IV change P&L")
    delta_pnl: float = Field(0.0, description="Directional P&L")
    
    # Returns
    return_pct: float = Field(0.0, description="% return on capital")
    annualized_return: float = Field(0.0, description="Annualized %")
    sharpe_ratio: Optional[float] = Field(None, description="Risk-adjusted return")
    max_drawdown: float = Field(0.0, description="Worst case P&L")
    
    # Current Greeks  
    current_delta: float = Field(0.0)
    current_theta: float = Field(0.0)
    current_vega: float = Field(0.0)
    
    # Exit strategy
    target_profit: float = Field(0.0, description="Close at this P&L")
    stop_loss: float = Field(0.0, description="Close if P&L drops to this")
    time_exit: Optional[datetime] = Field(None, description="Close by this date")
    exit_reason: str = Field("", description="Why was it closed")
    
    status: str = Field("ACTIVE", description="ACTIVE, CLOSED, EXPIRED")
    closed_at: Optional[datetime] = Field(None)
    final_pnl: Optional[float] = Field(None, description="Actual P&L when closed")


class VolatilityProfile(BaseModel):
    """
    Volatility regime and arbitrage tracking.
    
    波动率体制和套利机会跟踪。
    """
    profile_id: str = Field(description="Unique ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ticker: str = Field(description="Which security")
    
    # Implied volatility
    iv_30d: float = Field(0.0, description="30-day IV", ge=0.0)
    iv_60d: float = Field(0.0, description="60-day IV", ge=0.0)
    iv_90d: float = Field(0.0, description="90-day IV", ge=0.0)
    iv_term_structure: str = Field("FLAT", description="UPWARD_SLOPING, FLAT, INVERTED")
    
    # Realized volatility
    realized_vol_20d: float = Field(0.0, description="Last 20 days", ge=0.0)
    realized_vol_60d: float = Field(0.0, description="Last 60 days", ge=0.0)
    
    # Skew and surface
    put_call_skew: float = Field(0.0, description="OTM put IV vs call IV")
    volatility_smile: Dict[str, float] = Field(default_factory=dict, description="IV by strike")
    
    # Historical context
    iv_percentile: float = Field(50.0, description="0-100 IV rank", ge=0.0, le=100.0)
    iv_high_52w: float = Field(0.0, description="52-week high", ge=0.0)
    iv_low_52w: float = Field(0.0, description="52-week low", ge=0.0)
    
    # Arbitrage
    iv_vs_rv_spread: float = Field(0.0, description="(IV - RV) in bps")
    calendar_spread_available: bool = Field(False, description="Calendar arb available?")
    butterfly_available: bool = Field(False, description="Butterfly arb available?")
    skew_arbitrage: float = Field(0.0, description="Skew spread value")
    
    # Forecast
    vol_forecast_7d: float = Field(0.0, description="1-week forecast", ge=0.0)
    vol_forecast_30d: float = Field(0.0, description="1-month forecast", ge=0.0)
    vol_direction_bias: str = Field("STABLE", description="UP, DOWN, STABLE")
    
    recommendation: str = Field("", description="VIX level and strategy suggestion")


class PairCorrelation(BaseModel):
    """
    Track correlations for pair trading strategies.
    
    跟踪配对交易的相关性。
    """
    pair_id: str = Field(description="Unique pair ID")
    ticker1: str = Field(description="First security")
    ticker2: str = Field(description="Second security")
    correlation_period_days: int = Field(60, description="Calculated over how long")
    
    # Correlation metrics
    correlation_60d: float = Field(0.0, description="60-day correlation", ge=-1.0, le=1.0)
    correlation_252d: float = Field(0.0, description="Long-term correlation", ge=-1.0, le=1.0)
    covariance_60d: float = Field(0.0, description="Covariance")
    beta_1_vs_2: float = Field(1.0, description="Beta of ticker1 vs ticker2")
    
    # Spread analysis
    current_spread: float = Field(0.0, description="Ticker1 - Ticker2 ratio")
    mean_spread: float = Field(0.0, description="Historical mean")
    std_spread: float = Field(1.0, description="Std deviation", gt=0.0)
    zscore_spread: float = Field(0.0, description="How many stds from mean")
    
    # Mean reversion
    halflife_days: int = Field(30, description="Days to mean revert")
    mean_revert_probability: float = Field(0.5, description="% likely to revert", ge=0.0, le=1.0)
    
    # Strategy
    current_trade: str = Field("NONE", description="LONG_1_SHORT_2, LONG_2_SHORT_1, NONE")
    entry_zscore: float = Field(2.0, description="Entry zscore")
    exit_zscore: float = Field(0.5, description="Exit zscore")
    
    # Execution
    shares_1: int = Field(0, description="Qty of ticker1")
    shares_2: int = Field(0, description="Qty of ticker2")
    hedge_ratio: float = Field(1.0, description="Beta hedge ratio", gt=0.0)
    
    status: str = Field("MONITORING", description="MONITORING, ACTIVE_TRADE, CLOSED")
    entry_date: Optional[datetime] = Field(None)
    exit_date: Optional[datetime] = Field(None)
    pnl: Optional[float] = Field(None, description="If closed")
    
    next_review: datetime = Field(default_factory=datetime.utcnow)


__all__ = [
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
