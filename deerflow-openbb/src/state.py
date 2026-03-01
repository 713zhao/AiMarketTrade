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

    # Graph execution metadata
    active_nodes: List[str] = Field(default_factory=list)
    completed_nodes: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=dict)

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
