"""
State schema for the deerflow multi-agent trading system.

Defines the data structures that flow through the graph, enabling
type-safe communication between agents and nodes.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


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


# ============================================================================
# PHASE 5: Production Deployment & Real-Time Integration
# ============================================================================

class BacktestPeriod(BaseModel):
    """
    Historical backtest period results.
    """
    period_id: int = Field(description="Period identifier")
    start_date: datetime = Field(description="Period start date")
    end_date: datetime = Field(description="Period end date")
    
    # Returns
    portfolio_return: float = Field(0.0, description="Portfolio return in period")
    benchmark_return: float = Field(0.0, description="Benchmark return")
    outperformance: float = Field(0.0, description="Active return vs benchmark")
    
    # Risk metrics
    volatility: float = Field(0.0, description="Period volatility")
    max_drawdown: float = Field(0.0, description="Maximum drawdown in period")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio")
    
    # Transactions
    num_trades: int = Field(0, description="Number of trades executed")
    total_costs: float = Field(0.0, description="Total transaction costs")
    turnover: float = Field(0.0, description="Portfolio turnover")


class BacktestResult(BaseModel):
    """
    Complete backtest validation of trading strategy.
    
    用于验证交易策略的完整回测结果。包含历史性能指标、
    风险分析、成本估算和周期性数据。
    """
    backtest_id: str = Field(description="Unique backtest identifier")
    backtest_name: str = Field(description="Descriptive name")
    backtest_start_date: datetime = Field(description="Backtest period start")
    backtest_end_date: datetime = Field(description="Backtest period end")
    backtest_days: int = Field(0, description="Number of trading days")
    
    # Holdings and rebalancing
    starting_portfolio: Dict[str, float] = Field(default_factory=dict)
    ending_portfolio: Dict[str, float] = Field(default_factory=dict)
    rebalance_frequency: str = Field("monthly", description="monthly, quarterly, etc.")
    
    # Overall results
    total_return: float = Field(0.0, description="Cumulative total return")
    annualized_return: float = Field(0.0, description="Annualized return (%)")
    total_volatility: float = Field(0.0, description="Cumulative volatility")
    annualized_volatility: float = Field(0.0, description="Annualized volatility (%)")
    sharpe_ratio: float = Field(0.0, description="Overall Sharpe ratio")
    sortino_ratio: float = Field(0.0, description="Downside risk adjusted")
    
    # Benchmark comparison
    benchmark_return: float = Field(0.0, description="Benchmark total return")
    benchmark_volatility: float = Field(0.0, description="Benchmark volatility")
    outperformance: float = Field(0.0, description="Active return vs benchmark")
    tracking_error: float = Field(0.0, description="Active risk vs benchmark")
    information_ratio: float = Field(0.0, description="Outperformance / tracking error")
    
    # Drawdown analysis
    max_drawdown: float = Field(0.0, description="Maximum drawdown")
    max_drawdown_duration: int = Field(0, description="Longest recovery in days")
    num_drawdowns_20pct: int = Field(0, description="Drawdowns >20%")
    
    # Execution analysis
    total_trades: int = Field(0, description="Total transaction count")
    total_costs: float = Field(0.0, description="Total transaction costs")
    avg_cost_per_trade: float = Field(0.0, description="Average cost per trade")
    total_turnover: float = Field(0.0, description="Total turnover")
    
    # Period-by-period results
    periods: List[BacktestPeriod] = Field(default_factory=list)
    
    # Worst/best periods
    worst_month: float = Field(0.0, description="Worst monthly return")
    best_month: float = Field(0.0, description="Best monthly return")
    positive_months: int = Field(0, description="Months with positive return")
    total_months: int = Field(0, description="Total months in backtest")
    
    # Robustness
    stress_test_return: float = Field(0.0, description="Return in worst scenario")
    recovery_time_avg: float = Field(0.0, description="Average recovery time (days)")
    
    # Summary
    summary: str = Field("", description="Backtest summary")
    conclusion: str = Field("", description="Recommended actions based on backtest")


class EfficientFrontierData(BaseModel):
    """
    Multiple portfolios spanning the efficient frontier.
    
    提供位于有效边界上的多个投资组合，从最低风险到
    风险偏好组合。包括特殊投资组合和约束分析。
    """
    num_portfolios: int = Field(50, description="Number of portfolios on frontier")
    min_return: float = Field(0.0, description="Minimum return on frontier")
    max_return: float = Field(0.20, description="Maximum return on frontier")
    
    # Portfolios
    portfolios: List[EfficientFrontierPoint] = Field(default_factory=list)
    
    # Special portfolios
    global_minimum_variance: Optional[EfficientFrontierPoint] = Field(None, description="Lowest risk portfolio")
    maximum_sharpe_portfolio: Optional[EfficientFrontierPoint] = Field(None, description="Best risk-adjusted portfolio")
    current_portfolio: Optional[EfficientFrontierPoint] = Field(None, description="Current allocation")
    
    # Constraint analysis
    constraints_active: List[str] = Field(default_factory=list, description="Which constraints are binding")
    constraint_impacts: Dict[str, float] = Field(default_factory=dict, description="Performance impact of constraints")
    
    # Summary
    summary: str = Field("", description="Frontier analysis summary")


class TransactionExecutionPlan(BaseModel):
    """
    Detailed execution plan with transaction costs and timing.
    
    执行计划，包括交易详情、成本估算和执行策略。
    """
    execution_id: str = Field(description="Unique execution identifier")
    execution_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Trades
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="Individual trades with details")
    
    # Cost estimation
    estimated_commission: float = Field(0.0, description="Estimated commission costs")
    estimated_market_impact: float = Field(0.0, description="Estimated market impact")
    estimated_slippage: float = Field(0.0, description="Estimated execution slippage")
    estimated_opportunity_cost: float = Field(0.0, description="Cost of delayed execution")
    total_estimated_cost: float = Field(0.0, description="Total estimated costs")
    total_cost_bps: float = Field(0.0, description="Costs in basis points (0.01%)")
    
    # Execution strategy
    execution_strategy: str = Field("vwap", description="Execution algorithm: vwap, twap, direct, etc")
    execution_timeline: str = Field("1 day", description="How quickly to execute")
    market_hours_only: bool = Field(True, description="Limit to market hours?")
    
    # Constraints
    max_order_size: float = Field(0.1, description="Max order as % of daily volume")
    avoid_news: bool = Field(True, description="Avoid execution around earnings?")
    tax_aware: bool = Field(True, description="Consider tax-loss harvesting?")
    
    # Summary
    summary: str = Field("", description="Execution plan summary")


class PortfolioSnapshot(BaseModel):
    """
    Real-time portfolio state and metrics snapshot.
    
    实时投资组合状态快照，包括头寸、风险指标和性能。
    """
    snapshot_id: str = Field(description="Unique snapshot identifier")
    snapshot_time: datetime = Field(default_factory=datetime.utcnow)
    
    # Current holdings
    current_positions: Dict[str, float] = Field(default_factory=dict, description="Current holdings by ticker")
    target_positions: Dict[str, float] = Field(default_factory=dict, description="Target allocations")
    
    # Position metrics
    position_values: Dict[str, float] = Field(default_factory=dict, description="Current value by position")
    position_returns: Dict[str, float] = Field(default_factory=dict, description="Return of each position")
    position_drift: Dict[str, float] = Field(default_factory=dict, description="Drift from target")
    
    # Portfolio metrics
    total_value: float = Field(0.0, description="Total portfolio value")
    cash_position: float = Field(0.0, description="Cash & equivalents")
    gross_exposure: float = Field(0.0, description="Long + abs(short)")
    net_exposure: float = Field(0.0, description="Long - short")
    leverage_ratio: float = Field(1.0, description="Gross / (gross + short)")
    
    # Risk metrics (real-time)
    portfolio_volatility: float = Field(0.0, description="Current portfolio volatility")
    portfolio_beta: float = Field(1.0, description="Market beta")
    portfolio_value_at_risk: float = Field(0.0, description="Current VaR")
    portfolio_drawdown: float = Field(0.0, description="Current drawdown from peak")
    
    # Performance (YTD/since inception)
    ytd_return: float = Field(0.0, description="Year-to-date return")
    inception_return: float = Field(0.0, description="Total return since inception")
    monthly_return: float = Field(0.0, description="Current month return")
    daily_return: float = Field(0.0, description="Today's return")
    
    # Alert flags
    rebalancing_needed: bool = Field(False, description="Drift triggers rebalancing?")
    risk_threshold_exceeded: bool = Field(False, description="Risk above limits?")
    cash_needed: bool = Field(False, description="Margin call or cash needed?")


class LiveTradingSession(BaseModel):
    """
    Real-time active trading session state.
    
    实时交易会话，追踪执行的交易和性能指标。
    """
    session_id: str = Field(description="Unique session identifier")
    session_start: datetime = Field(description="Session start time")
    session_end: Optional[datetime] = Field(None, description="Session end time")
    
    # Portfolio state
    starting_portfolio: Dict[str, float] = Field(default_factory=dict)
    current_portfolio: Dict[str, float] = Field(default_factory=dict)
    starting_value: float = Field(0.0, description="Portfolio value at session start")
    current_value: float = Field(0.0, description="Current portfolio value")
    session_pnl: float = Field(0.0, description="Session profit/loss")
    session_pnl_pct: float = Field(0.0, description="Session return (%)")
    
    # Trading activity
    trades_executed: List[Dict[str, Any]] = Field(default_factory=list, description="Executed trades")
    pending_trades: List[Dict[str, Any]] = Field(default_factory=list, description="Pending order queue")
    rejected_trades: List[Dict[str, Any]] = Field(default_factory=list, description="Failed executions")
    
    # Execution metrics
    total_commissions: float = Field(0.0, description="Total execution costs")
    total_slippage: float = Field(0.0, description="Total slippage vs target")
    total_market_impact: float = Field(0.0, description="Total market impact")
    
    # Status
    is_active: bool = Field(True, description="Is session currently active?")
    error_count: int = Field(0, description="Number of errors in session")
    last_error: Optional[str] = Field(None, description="Most recent error message")


class PerformanceMetricsSnapshot(BaseModel):
    """
    Comprehensive real-time performance metrics snapshot.
    
    完整的实时性能指标，包括收益、风险和风险调整指标。
    """
    metrics_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Returns
    daily_return: float = Field(0.0, description="Daily return")
    weekly_return: float = Field(0.0, description="Weekly return")
    monthly_return: float = Field(0.0, description="Current month-to-date")
    ytd_return: float = Field(0.0, description="Year-to-date")
    inception_return: float = Field(0.0, description="Total return since inception")
    
    # Risk
    daily_volatility: float = Field(0.0, description="Daily volatility")
    rolling_volatility_20d: float = Field(0.0, description="20-day rolling volatility")
    rolling_volatility_60d: float = Field(0.0, description="60-day rolling volatility")
    current_drawdown: float = Field(0.0, description="From peak drawdown")
    max_drawdown_20d: float = Field(0.0, description="Max DD in last 20 days")
    max_drawdown_60d: float = Field(0.0, description="Max DD in last 60 days")
    
    # Risk-adjusted
    sharpe_ratio_daily: float = Field(0.0, description="Daily Sharpe ratio")
    sharpe_ratio_annual: float = Field(0.0, description="Annualized Sharpe ratio")
    sortino_ratio: float = Field(0.0, description="Downside risk adjusted")
    calmar_ratio: float = Field(0.0, description="Return / max drawdown")
    
    # Relative performance
    benchmark_return: float = Field(0.0, description="Benchmark return same period")
    outperformance: float = Field(0.0, description="Active return")
    tracking_error: float = Field(0.0, description="Active risk")
    information_ratio: float = Field(0.0, description="IR (outperformance/tracking error)")
    
    # Win rate
    positive_days: int = Field(0, description="Days with positive return")
    total_days: int = Field(0, description="Total trading days")
    win_rate: float = Field(0.0, description="Positive days %")
    best_day: float = Field(0.0, description="Best daily return")
    worst_day: float = Field(0.0, description="Worst daily return")
    avg_winning_day: float = Field(0.0, description="Average positive return")
    avg_losing_day: float = Field(0.0, description="Average negative return")



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
    "get_settings",
]
