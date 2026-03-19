"""
Ticker data and analysis models (Phase 1-2).

Raw market data and initial analysis results for individual securities.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from .base import AnalystType, DataProvider


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


__all__ = [
    "TickerData",
    "TechnicalAnalysis",
    "FundamentalAnalysis",
    "NewsAnalysis",
]
