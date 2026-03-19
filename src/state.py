"""
State schema for the deerflow multi-agent trading system.

Defines the data structures that flow through the graph, enabling
type-safe communication between agents and nodes.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from typing_extensions import Annotated, TypedDict
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


def _reduce_session_id(left: str | None, right: str | None) -> str | None:
    """Reducer function for concurrent session_id updates in LandGraph.
    
    Returns the rightmost non-None/non-empty value, or left if right is empty.
    """
    if right and right.strip():
        return right
    return left if left else ""


class AnalystType(str, Enum):
    """Types of analyst agents in the system."""
    NEWS = "news"
    TECHNICAL = "technical"
    FUNDAMENTALS = "fundamentals"
    GROWTH = "growth"
    MACRO = "macro"
    RISK = "risk"
    PORTFOLIO = "portfolio"
    PORTFOLIO_RISK = "portfolio_risk"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"


class SignalType(str, Enum):
    """Trading signal direction."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class DataProvider(str, Enum):
    """Supported data providers."""
    FMP = "fmp"
    POLYGON = "polygon"
    YAHOO = "yahoo"
    ALPHA_VANTAGE = "alpha_vantage"
    EODHD = "eodhd"


class TickerData(BaseModel):
    """
    Raw data fetched for a single ticker from OpenBB.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ticker: str
    provider: DataProvider
    timeframe: str = "1d"  # daily, 1h, 15m, etc.

    # Price data (DataFrame converted to dict for serialization)
    historical_data: Dict[str, List[Any]] = Field(
        default_factory=dict,
        description="OHLCV historical data with date index"
    )

    # Fundamental data
    company_info: Dict[str, Any] = Field(default_factory=dict)
    financial_statements: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    key_metrics: Dict[str, Any] = Field(default_factory=dict)

    # News data
    news: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: float = Field(1.0, ge=0.0, le=1.0)

    def has_sufficient_data(self, min_points: int = 252) -> bool:
        """Check if historical data has sufficient points for analysis."""
        if not self.historical_data:
            return False
        # Assuming 'close' or similar price column exists
        price_key = next((k for k in self.historical_data.keys()
                         if 'close' in k.lower() or 'price' in k.lower()), None)
        if price_key:
            return len(self.historical_data[price_key]) >= min_points
        return len(next(iter(self.historical_data.values()), [])) >= min_points


class TechnicalAnalysis(BaseModel):
    """
    Results from technical analysis agent.
    """
    ticker: str

    # Calculated indicators
    indicators: Dict[str, List[float]] = Field(default_factory=dict)

    # Signal generation
    signals: List[Dict[str, Any]] = Field(default_factory=list)

    # Pattern recognition
    patterns: List[Dict[str, Any]] = Field(default_factory=list)

    # Support/Resistance levels
    support_levels: List[float] = Field(default_factory=list)
    resistance_levels: List[float] = Field(default_factory=list)

    # Trend analysis
    trend: str = Field("neutral", description="bullish, bearish, or neutral")
    trend_strength: float = Field(0.5, ge=0.0, le=1.0)

    # Momentum
    momentum: str = Field("neutral", description="overbought, oversold, or neutral")
    rsi_value: Optional[float] = Field(None, ge=0.0, le=100.0)

    # Volatility
    volatility: float = Field(0.0, ge=0.0, description="Annualized volatility")

    # Summary
    summary: str = Field("", description="Narrative summary of technical analysis")

    # Confidence score
    confidence: float = Field(0.5, ge=0.0, le=1.0)

    analyst_type: AnalystType = AnalystType.TECHNICAL


class FundamentalAnalysis(BaseModel):
    """
    Results from fundamental analysis agent.
    """
    ticker: str

    # Key financial metrics
    pe_ratio: Optional[float] = Field(None, description="Price-to-Earnings ratio")
    pb_ratio: Optional[float] = Field(None, description="Price-to-Book ratio")
    ps_ratio: Optional[float] = Field(None, description="Price-to-Sales ratio")
    peg_ratio: Optional[float] = Field(None, description="PEG ratio")

    # Profitability metrics
    roe: Optional[float] = Field(None, description="Return on Equity (%)")
    roa: Optional[float] = Field(None, description="Return on Assets (%)")
    net_margin: Optional[float] = Field(None, description="Net Profit Margin (%)")
    operating_margin: Optional[float] = Field(None, description="Operating Margin (%)")

    # Growth metrics
    revenue_growth: Optional[float] = Field(None, description="Revenue Growth (%)")
    eps_growth: Optional[float] = Field(None, description="EPS Growth (%)")

    # Financial health
    debt_to_equity: Optional[float] = Field(None, description="Debt-to-Equity ratio")
    current_ratio: Optional[float] = Field(None, description="Current ratio")
    free_cash_flow: Optional[float] = Field(None, description="Free Cash Flow")

    # Valuation assessment
    valuation: str = Field("fair", description="undervalued, fair, overvalued")
    fair_value_estimate: Optional[float] = Field(None)

    # Strengths and weaknesses
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)

    # Summary
    summary: str = Field("", description="Narrative summary of fundamental analysis")

    # Confidence
    confidence: float = Field(0.5, ge=0.0, le=1.0)

    analyst_type: AnalystType = AnalystType.FUNDAMENTALS


class NewsAnalysis(BaseModel):
    """
    Results from news sentiment analysis agent.
    """
    ticker: str

    # Sentiment aggregation
    overall_sentiment: float = Field(
        0.0,
        ge=-1.0,
        le=1.0,
        description="Overall sentiment score (-1 bearish to +1 bullish)"
    )
    sentiment_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Sentiment by source/category"
    )

    # News volume
    news_volume: int = Field(0, description="Number of news articles analyzed")
    recent_news_count: int = Field(0, description="News articles in last 7 days")

    # Key catalysts identified
    catalysts: List[Dict[str, Any]] = Field(default_factory=list)

    # Key events and their impact
    key_events: List[Dict[str, Any]] = Field(default_factory=list)

    # Risk events
    risk_events: List[Dict[str, Any]] = Field(default_factory=list)

    # Entity mentions (companies, people, products)
    key_entities: List[str] = Field(default_factory=list)

    # Summary
    summary: str = Field("", description="Narrative summary of news analysis")

    # Confidence
    confidence: float = Field(0.5, ge=0.0, le=1.0)

    analyst_type: AnalystType = AnalystType.NEWS


class GrowthAnalysis(BaseModel):
    """
    Results from growth potential analysis agent.
    """
    ticker: str

    # Revenue growth trajectory
    revenue_growth_rate: Optional[float] = Field(
        None,
        description="CAGR revenue growth (%)"
    )
    revenue_growth_trend: str = Field("stable", description="accelerating, stable, decelerating")

    # Earnings growth
    eps_growth_rate: Optional[float] = Field(
        None,
        description="CAGR EPS growth (%)"
    )
    eps_growth_trend: str = Field("stable")

    # Future estimates (from analyst consensus)
    next_quarter_estimate: Optional[float] = Field(None)
    next_year_estimate: Optional[float] = Field(None)
    long_term_growth_rate: Optional[float] = Field(None)

    # Market opportunity
    addressable_market_size: Optional[float] = Field(None)
    market_share: Optional[float] = Field(None)
    market_growth_rate: Optional[float] = Field(None)

    # Innovation metrics
    rd_to_revenue: Optional[float] = Field(None, description="R&D as % of revenue")
    patent_count: Optional[int] = Field(None)

    # Customer growth
    customer_growth_rate: Optional[float] = Field(None)

    # Management guidance
    guidance_range: Optional[Dict[str, float]] = Field(None)

    # Growth score (0-100)
    growth_score: float = Field(50.0, ge=0.0, le=100.0)

    # Summary
    summary: str = Field("", description="Narrative summary of growth analysis")

    # Confidence
    confidence: float = Field(0.5, ge=0.0, le=1.0)

    analyst_type: AnalystType = AnalystType.GROWTH


class RiskAnalysis(BaseModel):
    """
    Results from risk assessment agent.
    """
    ticker: str

    # Systematic risk
    beta: Optional[float] = Field(None, description="Market beta")
    alpha: Optional[float] = Field(None, description="Jensen's alpha")

    # Volatility metrics
    volatility: float = Field(0.0, ge=0.0, description="Annualized volatility")
    var_95: Optional[float] = Field(None, description="Value at Risk (95% confidence)")
    cvar_95: Optional[float] = Field(None, description="Conditional VaR")

    # Drawdown risk
    max_drawdown: Optional[float] = Field(None, description="Maximum historical drawdown")
    current_drawdown: Optional[float] = Field(None, description="Current drawdown from peak")

    # Liquidity risk
    average_volume: Optional[float] = Field(None, description="Average daily volume")
    bid_ask_spread: Optional[float] = Field(None, description="Average bid-ask spread")

    # Financial risk
    debt_to_equity: Optional[float] = Field(None)
    interest_coverage: Optional[float] = Field(None)
    working_capital_ratio: Optional[float] = Field(None)

    # Concentration risk
    major_shareholder_percentage: Optional[float] = Field(None)

    # Regulatory/Sector risks
    sector_risks: List[str] = Field(default_factory=list)
    regulatory_risks: List[str] = Field(default_factory=list)

    # Risk score (0-100, higher = riskier)
    risk_score: float = Field(50.0, ge=0.0, le=100.0)

    # Risk level classification
    risk_level: str = Field("medium", description="low, medium, high")

    # Summary
    summary: str = Field("", description="Narrative summary of risk analysis")

    # Confidence
    confidence: float = Field(0.5, ge=0.0, le=1.0)

    analyst_type: AnalystType = AnalystType.RISK


class MacroAnalysis(BaseModel):
    """
    Results from macroeconomic analysis agent.
    """
    ticker: str
    sector: str = Field("", description="Company sector")

    # Interest rate environment
    interest_rate_trend: str = Field("neutral", description="rising, falling, stable")

    # Inflation
    inflation_rate: Optional[float] = Field(None, description="Current inflation rate")
    inflation_trend: str = Field("stable")

    # GDP growth
    gdp_growth: Optional[float] = Field(None, description="GDP growth rate")
    economic_outlook: str = Field("neutral", description="expansionary, contractionary, neutral")

    # Unemployment
    unemployment_rate: Optional[float] = Field(None)

    # Consumer sentiment
    consumer_sentiment: Optional[float] = Field(None)

    # Sector rotation
    sector_rotation: str = Field("neutral", description="favoring, rotating out, neutral")

    # Currency impact (if multinational)
    currency_impact: str = Field("neutral")

    # Regulatory environment
    regulatory_factors: List[str] = Field(default_factory=list)

    # Macro score (0-100, higher = more favorable)
    macro_score: float = Field(50.0, ge=0.0, le=100.0)

    # Summary
    summary: str = Field("", description="Narrative summary of macro analysis")

    # Confidence
    confidence: float = Field(0.5, ge=0.0, le=1.0)

    analyst_type: AnalystType = AnalystType.MACRO


class ConsensusSignal(BaseModel):
    """
    Consensus across all analysts for a single ticker.
    """
    ticker: str

    # Aggregate scores
    overall_signal: SignalType = Field(SignalType.HOLD)
    signal_strength: float = Field(0.0, ge=0.0, le=1.0,
                                   description="Strength of consensus (0-1)")

    # Analyst contributions
    analyst_signals: Dict[AnalystType, Dict[str, Any]] = Field(default_factory=dict)

    # Weighted scores
    technical_weight: float = 0.2
    fundamental_weight: float = 0.25
    news_weight: float = 0.15
    growth_weight: float = 0.15
    risk_weight: float = -0.15  # Negative weight (higher risk = lower score)
    macro_weight: float = 0.1

    # Final recommendation
    target_price: Optional[float] = Field(None)
    time_horizon: str = Field("MEDIUM")
    expected_return: Optional[float] = Field(None)

    # Confidence in consensus
    consensus_confidence: float = Field(0.5, ge=0.0, le=1.0)


class TradingDecision(BaseModel):
    """
    Final trading decision for execution.
    """
    ticker: str

    # Decision
    action: SignalType
    position_size: float = Field(0.0, ge=0.0, le=100.0,
                                description="Position size as % of portfolio")

    # Risk management
    stop_loss: Optional[float] = Field(None)
    take_profit: Optional[float] = Field(None)
    risk_reward_ratio: Optional[float] = Field(None)

    # Rationale
    rationale: str = Field("", description="Detailed explanation of decision")

    # Confidence
    confidence: float = Field(0.5, ge=0.0, le=1.0)

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScenarioAnalysis(BaseModel):
    """
    Monte Carlo scenario analysis for portfolio risk assessment.
    """
    scenario_id: int = Field(description="Scenario number")
    
    # Scenario parameters
    days_ahead: int = Field(30, description="Days forward in scenario")
    returns: Dict[str, float] = Field(default_factory=dict, description="Simulated returns by ticker")
    prices: Dict[str, float] = Field(default_factory=dict, description="Simulated end prices by ticker")
    portfolio_return: float = Field(0.0, description="Aggregated portfolio return")
    
    # Risk metrics for this scenario
    portfolio_value_change: float = Field(0.0, description="Change in portfolio value")
    max_realized_loss: float = Field(0.0, description="Maximum loss during scenario")


class PortfolioRiskAnalysis(BaseModel):
    """
    Portfolio-level risk assessment combining all positions.
    """
    # Risk aggregation
    portfolio_volatility: float = Field(0.0, ge=0.0, description="Portfolio volatility (annualized)")
    diversification_ratio: float = Field(1.0, ge=0.0, description="Portfolio vol / avg ticker vol")
    
    # Correlation analysis
    average_correlation: float = Field(0.0, description="Average pairwise correlation")
    max_correlation: float = Field(1.0, description="Highest correlation pair")
    min_correlation: float = Field(-1.0, description="Lowest correlation pair")
    
    # Monte Carlo results (1000 simulations)
    simulated_returns: List[float] = Field(default_factory=list, description="Distribution of returns")
    monte_carlo_var: float = Field(0.0, description="Value at Risk (95%) from MC simulation")
    monte_carlo_cvar: float = Field(0.0, description="Conditional VaR from MC simulation")
    
    # Drawdown analysis
    expected_maximum_drawdown: float = Field(0.0, description="Expected max drawdown in scenario")
    drawdown_percentile_95: float = Field(0.0, description="95th percentile drawdown")
    
    # Concentration risk
    herfindahl_index: float = Field(0.0, ge=0.0, le=1.0, description="Portfolio concentration (HHI)")
    largest_position: float = Field(0.0, description="Size of largest position (%)")
    effective_number_of_bets: float = Field(0.0, ge=0.0, description="Effective diversification count")
    
    # Stress testing
    stress_scenario_returns: Dict[str, float] = Field(
        default_factory=dict,
        description="Portfolio returns under stressed conditions"
    )
    
    # Summary
    summary: str = Field("", description="Narrative summary of portfolio risk")
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    analyst_type: AnalystType = AnalystType.PORTFOLIO_RISK


class PortfolioOptimizationResult(BaseModel):
    """
    Optimized position sizing and asset allocation from portfolio optimization.
    """
    # Optimization parameters used
    optimization_method: str = Field("kelly", description="Method: kelly, volatility_targeting, efficient_frontier")
    target_volatility: Optional[float] = Field(None, description="Target portfolio volatility if vol targeting")
    risk_free_rate: float = Field(0.02, description="Risk-free rate for Sharpe ratio and Kelly")
    
    # Optimized positions
    optimized_positions: Dict[str, float] = Field(
        default_factory=dict,
        description="Recommended position sizes by ticker (% of portfolio)"
    )
    
    # Position constraints applied
    max_single_position: float = Field(30.0, description="Max allowed per position (%)")
    min_position_for_inclusion: float = Field(0.5, description="Min size to include a position (%)")
    leverage_allowed: bool = Field(False, description="Whether leverage/shorting is allowed")
    
    # Kelly-specific metrics
    kelly_fractions: Dict[str, float] = Field(default_factory=dict, description="Full Kelly fraction per ticker")
    fractional_kelly_factor: float = Field(0.25, description="Fraction of Kelly applied (e.g., 0.25 for 1/4 Kelly)")
    
    # Expected portfolio metrics
    expected_return: float = Field(0.0, description="Expected annual return of optimized portfolio")
    optimized_volatility: float = Field(0.0, description="Volatility of optimized portfolio")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio of optimized portfolio")
    
    # Risk metrics
    portfolio_var_95: float = Field(0.0, description="Portfolio VAR at 95% confidence")
    expected_shortfall: float = Field(0.0, description="Expected shortfall (CVaR)")
    
    # Diversification metrics
    portfolio_hhi: float = Field(0.0, description="Herfindahl index of optimized portfolio")
    effective_bets: float = Field(0.0, description="Effective number of independent bets")
    
    # Constraints satisfaction
    constraints_met: bool = Field(True, description="Whether all constraints were satisfiable")
    constraint_violations: List[str] = Field(default_factory=list, description="Any constraints that couldn't be met")
    
    # Summary
    summary: str = Field("", description="Narrative summary of optimization results")
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    analyst_type: AnalystType = AnalystType.PORTFOLIO_OPTIMIZATION


# Forward declaration of classes needed by DeerflowState
class MarketRegime(str, Enum):
    """Classification of market regime."""
    BULL_HIGH_VOL = "bull_high_vol"      # Strong but volatile
    BULL_LOW_VOL = "bull_low_vol"        # Steady growth
    BEAR_HIGH_VOL = "bear_high_vol"      # Declining volatility rising
    BEAR_LOW_VOL = "bear_low_vol"        # Stable decline
    SIDEWAYS = "sideways"                # Ranging market
    CRISIS = "crisis"                    # Market stress/crash


class MacroScenario(BaseModel):
    """
    Macroeconomic scenario for multi-scenario analysis.
    
    Represents a plausible future economic environment and
    its implications for market returns and sector performance.
    """
    scenario_id: int = Field(description="Unique scenario identifier")
    scenario_name: str = Field(description="Descriptive name (e.g., 'Soft Landing', 'Stagflation')")
    probability: float = Field(0.25, ge=0.0, le=1.0, description="Probability of scenario (0-1)")
    
    # Economic assumptions
    gdp_growth: float = Field(0.0, description="Expected GDP growth rate")
    inflation_rate: float = Field(0.0, description="Expected inflation rate")
    unemployment_rate: float = Field(0.05, description="Expected unemployment rate")
    interest_rate: float = Field(0.04, description="Expected policy rate (10yr equivalent)")
    
    # Market environment
    market_regime: "MarketRegime" = Field(MarketRegime.SIDEWAYS, description="Regime classification")
    volatility_expectation: float = Field(0.15, description="Expected market volatility")
    correlation_expectation: float = Field(0.4, description="Expected avg stock correlation")
    
    # Sector impacts (returns relative to base case)
    sector_impacts: Dict[str, float] = Field(
        default_factory=dict,
        description="Expected return adjustments by sector (%)"
    )
    
    # Asset class impacts
    equity_premium: float = Field(0.06, description="Equity risk premium")
    bond_yield: float = Field(0.03, description="Expected 10yr bond yield")
    commodity_price_change: float = Field(0.0, description="Commodity price % change")
    currency_volatility: float = Field(0.08, description="FX volatility")
    
    # Portfolio implications
    portfolio_return_forecast: float = Field(0.0, description="Expected portfolio return in scenario")
    portfolio_volatility_forecast: float = Field(0.15, description="Expected portfolio volatility")
    
    # Risk factors stressed
    stressed_factors: List[str] = Field(
        default_factory=list,
        description="Key factors stressed in this scenario"
    )
    
    # Description
    narrative: str = Field("", description="Scenario description and rationale")


class RebalancingRule(BaseModel):
    """
    Rebalancing decision based on portfolio drift and opportunity.
    """
    rule_id: int = Field(description="Rule identifier")
    rule_type: str = Field("threshold", description="drift_threshold, opportunity, scheduled")
    
    # Drift monitoring
    position_drift_threshold: float = Field(0.05, description="Rebalance if position drifts >5%")
    portfolio_drift_threshold: float = Field(0.10, description="Rebalance if portfolio drifts >10%")
    
    # Scheduled rebalancing
    rebalance_frequency: str = Field("monthly", description="monthly, quarterly, semi-annual")
    
    # Opportunity rebalancing
    volatility_spike_threshold: float = Field(0.30, description="Rebalance if vol spikes >30%")
    sector_rotation_threshold: float = Field(0.15, description="Rebalance on >15% sector rotation")
    
    # Execution
    max_turnover_per_rebalance: float = Field(0.20, description="Max 20% of portfolio turnover")
    tax_loss_harvesting: bool = Field(True, description="Harvest tax losses when rebalancing")
    
    # Current state
    should_rebalance: bool = Field(False, description="Rebalancing recommended?")
    rebalancing_rationale: str = Field("", description="Why rebalancing is/isn't needed")
    estimated_trades: List[Dict[str, Any]] = Field(default_factory=list, description="Proposed trades")


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


class MultiScenarioAnalysis(BaseModel):
    """
    Multi-scenario portfolio analysis.
    
    Analyzes portfolio performance under different macro scenarios
    and market regimes for robust decision-making.
    """
    scenarios: List[MacroScenario] = Field(default_factory=list, description="Macro scenarios")
    
    # Results per scenario
    scenario_portfolio_returns: Dict[int, float] = Field(
        default_factory=dict,
        description="Portfolio return in each scenario"
    )
    scenario_portfolio_volatility: Dict[int, float] = Field(
        default_factory=dict,
        description="Portfolio volatility in each scenario"
    )
    
    # Expected value calculation
    expected_return: float = Field(0.0, description="Probability-weighted expected return")
    expected_volatility: float = Field(0.0, description="Probability-weighted volatility")
    
    # Robust metrics
    worst_case_return: float = Field(0.0, description="Return in worst scenario")
    best_case_return: float = Field(0.0, description="Return in best scenario")
    return_range: float = Field(0.0, description="Spread between worst/best")
    
    # Robustness assessment
    scenario_resilience: float = Field(0.5, description="Resilience score (0-1, higher=more robust)")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improving robustness"
    )
    
    narrative: str = Field("", description="Multi-scenario analysis summary")


# Phase 5 model classes (needed before DeerflowState)
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
    initial_capital: float = Field(1000000, description="Starting capital")
    final_portfolio_value: float = Field(0.0, description="Ending portfolio value")
    total_return: float = Field(0.0, description="Cumulative total return")
    annualized_return: float = Field(0.0, description="Annualized return (%)")
    volatility: float = Field(0.0, description="Annualized volatility (%)")
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


class EfficientFrontierPoint(BaseModel):
    """Point on efficient frontier."""
    portfolio_id: int = Field(description="Portfolio identifier")
    expected_return: float = Field(0.0, description="Expected return")
    volatility: float = Field(0.15, description="Expected volatility")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio")
    portfolio_weights: Dict[str, float] = Field(default_factory=dict, description="Ticker weights")
    risk_adjusted_return: float = Field(0.0, description="Return/volatility")
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
    summary: str = Field("", description="Execution plan summary")


class PortfolioSnapshot(BaseModel):
    """Real-time portfolio state and metrics snapshot."""
    snapshot_id: str = Field(description="Unique snapshot identifier")
    snapshot_time: datetime = Field(default_factory=datetime.utcnow)
    current_positions: Dict[str, float] = Field(default_factory=dict, description="Current holdings")
    target_positions: Dict[str, float] = Field(default_factory=dict, description="Target allocations")
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
    current_drawdown: float = Field(0.0, description="Current drawdown")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio")
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


# ============================================================================
# PHASE 6: Broker API Integration & Live Trading - Define before DeerflowState
# ============================================================================

class BrokerAccount(BaseModel):
    """
    Broker account credentials and configuration.
    
    经纪账户凭证和配置：存储API密钥、账户设置和风险限制。
    """
    broker_id: str = Field(description="Broker identifier (alpaca, ib, etc)")
    account_id: str = Field(description="Broker account number")
    account_name: str = Field(description="Display name")
    is_live: bool = Field(False, description="Paper or live trading")
    base_url: str = Field("", description="API endpoint")
    max_daily_loss: float = Field(-0.02, description="Max daily loss % (-2%)")
    max_position_size: float = Field(0.10, description="Max capital % per position")
    max_leverage: float = Field(2.0, description="Max leverage allowed")
    last_validated: Optional[datetime] = Field(None, description="Last connection check")


class Order(BaseModel):
    """
    Pending or filled order details.
    
    订单详情：包括待执行和已成交订单。
    """
    order_id: str = Field(description="Unique order ID")
    broker_id: str = Field(description="Which broker")
    ticker: str = Field(description="Security symbol")
    order_type: str = Field(description="BUY, SELL, SHORT, COVER")
    execution_type: str = Field(description="MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP")
    quantity: int = Field(description="Shares/contracts")
    price: Optional[float] = Field(None, description="Limit price (if applicable)")
    stop_price: Optional[float] = Field(None, description="Stop price (if applicable)")
    status: str = Field(description="PENDING, SUBMITTED, FILLED, PARTIAL, CANCELLED, REJECTED")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = Field(None, description="Execution timestamp")
    filled_price: Optional[float] = Field(None, description="Actual execution price")
    filled_quantity: int = Field(0, description="Filled shares")
    commission: float = Field(0.0, description="Transaction cost")
    reason: str = Field("", description="Cancellation/rejection reason")


class BrokerPosition(BaseModel):
    """
    Active holdings in broker account.
    
    经纪账户中的活跃持仓。
    """
    position_id: str = Field(description="Unique position ID")
    broker_id: str = Field(description="Which broker")
    ticker: str = Field(description="Security symbol")
    quantity: int = Field(description="Current shares")
    avg_cost: float = Field(0.0, description="Average entry price")
    current_price: float = Field(0.0, description="Last market price")
    market_value: float = Field(0.0, description="Position value")
    unrealized_pnl: float = Field(0.0, description="Open P&L")
    realized_pnl: float = Field(0.0, description="Closed P&L")
    unrealized_pnl_pct: float = Field(0.0, description="P&L percentage")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Trade(BaseModel):
    """
    Completed trades (buy/sell pairs).
    
    已成交交易（买卖对）。
    """
    trade_id: str = Field(description="Unique trade ID")
    broker_id: str = Field(description="Which broker")
    ticker: str = Field(description="Security")
    entry_order_id: str = Field(description="Opens the trade")
    exit_order_id: Optional[str] = Field(None, description="Closes the trade")
    entry_price: float = Field(description="Entry execution price")
    exit_price: Optional[float] = Field(None, description="Exit price")
    quantity: int = Field(description="Shares")
    entry_time: datetime = Field(description="Entry timestamp")
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp")
    duration_seconds: Optional[int] = Field(None, description="Trade duration")
    gross_pnl: float = Field(0.0, description="P&L before costs")
    net_pnl: float = Field(0.0, description="P&L after commissions")
    entry_commission: float = Field(0.0, description="Buy commission")
    exit_commission: float = Field(0.0, description="Sell commission")
    status: str = Field("OPEN", description="OPEN, CLOSED, PARTIAL")
    notes: str = Field("", description="Entry reason, exit reason")


class BrokerAccountState(BaseModel):
    """
    Real-time broker account status and positions.
    
    实时经纪账户状态和持仓。
    """
    account_id: str = Field(description="Broker account ID")
    broker_id: str = Field(description="Broker identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Account metrics
    cash: float = Field(0.0, description="Available cash")
    buying_power: float = Field(0.0, description="Cash × (1 + leverage)")
    total_value: float = Field(0.0, description="Cash + portfolio value")
    portfolio_value: float = Field(0.0, description="Position values sum")
    day_trading_power: float = Field(0.0, description="Remaining day trade power")
    maintenance_requirement: float = Field(0.0, description="Collateral needed")
    maintenance_excess: float = Field(0.0, description="Excess collateral")
    equity_percent: float = Field(1.0, description="Equity as % of total")
    
    # Account status
    is_margin_call: bool = Field(False, description="Margin call flag")
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    
    # P&L
    unrealized_day_pnl: float = Field(0.0, description="Today's P&L")
    realized_day_pnl: float = Field(0.0, description="Today's realized P&L")
    realized_mtd_pnl: float = Field(0.0, description="Month-to-date realized")
    
    # Holdings
    open_positions: List[BrokerPosition] = Field(default_factory=list)
    pending_orders: List[Order] = Field(default_factory=list)
    recent_trades: List[Trade] = Field(default_factory=list)


class BrokerExecutionPlan(BaseModel):
    """
    Execution plan with broker routing.
    
    执行计划，包括经纪商路由。
    """
    execution_id: str = Field(description="Unique execution ID")
    plan_id: str = Field(description="From Phase 5 TransactionExecutionPlan")
    broker_id: str = Field(description="Selected broker")
    account_id: str = Field(description="Selected account")
    trades: List[Order] = Field(default_factory=list, description="Orders to execute")
    total_commission: float = Field(0.0, description="Expected total cost")
    execution_priority: str = Field("IMMEDIATE", description="Execution approach")
    max_slippage_bps: float = Field(10.0, description="Max slippage tolerance bps")
    time_limit_minutes: int = Field(60, description="Max time to execute all")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    status: str = Field("PLANNED", description="PLANNED, IN_PROGRESS, COMPLETED, FAILED, CANCELLED")
    filled_orders: List[Order] = Field(default_factory=list)
    execution_summary: str = Field("", description="Narrative of execution")


class ComplianceRecord(BaseModel):
    """
    Audit trail record for compliance and regulatory reporting.
    
    审计日志记录，用于合规和监管报告。
    """
    record_id: str = Field(description="Unique record ID")
    record_type: str = Field(description="ORDER_SUBMITTED, ORDER_FILLED, POSITION_OPENED, etc")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    broker_id: str = Field(description="Which broker")
    account_id: str = Field(description="Which account")
    
    # Event details
    ticker: Optional[str] = Field(None, description="Security symbol")
    order_id: Optional[str] = Field(None, description="Related order")
    trade_id: Optional[str] = Field(None, description="Related trade")
    
    # Values and state
    quantity: Optional[int] = Field(None, description="Trade quantity")
    price: Optional[float] = Field(None, description="Execution price")
    commission: Optional[float] = Field(None, description="Transaction cost")
    
    # Account state snapshot
    account_value_before: float = Field(0.0)
    account_value_after: float = Field(0.0)
    cash_before: float = Field(0.0)
    cash_after: float = Field(0.0)
    
    # Event description
    description: str = Field("", description="Event narrative")
    error: Optional[str] = Field(None, description="Any error message")


# ============================================================================
# PHASE 7: Advanced Strategies & Derivatives Trading
# ============================================================================

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
    delta: float = Field(description="Delta (directional sensitivity)", ge=-1.0, le=1.0)
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


class DeerflowState(BaseModel):
    """
    Master state object that flows through the entire deerflow graph.

    This is the primary state schema used by LangGraph to maintain
    context and pass data between nodes.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Session metadata - Annotated with reducer to handle concurrent LandGraph updates
    session_id: Annotated[str, _reduce_session_id] = Field("", description="Unique session identifier")
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


# Import and re-export for convenience
try:
    # Package context (when imported as deerflow_openbb module)
    from .config import get_settings
except ImportError:
    # Direct context (when imported directly)
    from config import get_settings



__all__ = [
    "AnalystType",
    "SignalType",
    "DataProvider",
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
    "DeerflowState",
    # Phase 4 additions
    "MarketRegime",
    "MacroScenario",
    "RebalancingRule",
    "PerformanceAttribution",
    "EfficientFrontierPoint",
    "MultiScenarioAnalysis",
    # Phase 5 additions
    "BacktestPeriod",
    "BacktestResult",
    "EfficientFrontierData",
    "TransactionExecutionPlan",
    "PortfolioSnapshot",
    "LiveTradingSession",
    "PerformanceMetricsSnapshot",
    # Phase 6 additions
    "BrokerAccount",
    "Order",
    "BrokerPosition",
    "Trade",
    "BrokerAccountState",
    "BrokerExecutionPlan",
    "ComplianceRecord",
    # Phase 7 additions
    "OptionContract",
    "FuturesContract",
    "CryptoDerivative",
    "MultiLegOrder",
    "GreeksSnapshot",
    "HedgeAllocation",
    "StrategyPerformance",
    "VolatilityProfile",
    "PairCorrelation",
    "get_settings",
]
