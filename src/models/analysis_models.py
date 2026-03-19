"""
Analysis and consensus models (Phase 2-3).

Analyst perspectives, consensus signals, and trading decisions.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .base import AnalystType, SignalType


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


__all__ = [
    "GrowthAnalysis",
    "RiskAnalysis",
    "MacroAnalysis",
    "ConsensusSignal",
    "TradingDecision",
    "ScenarioAnalysis",
]
