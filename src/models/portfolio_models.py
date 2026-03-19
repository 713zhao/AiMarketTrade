"""
Portfolio-level analysis and optimization models (Phase 3-4).

Portfolio risk analysis, optimization, and multi-scenario evaluation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .base import AnalystType, MarketRegime


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
    market_regime: MarketRegime = Field(MarketRegime.SIDEWAYS, description="Regime classification")
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


__all__ = [
    "PortfolioRiskAnalysis",
    "PortfolioOptimizationResult",
    "MacroScenario",
    "RebalancingRule",
    "MultiScenarioAnalysis",
]
