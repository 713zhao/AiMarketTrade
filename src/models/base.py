"""
Base enumerations and types for the deerflow trading system.

Defines shared enum types used throughout the system for type safety
and clear semantics.
"""

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


class MarketRegime(str, Enum):
    """Classification of market regime."""
    BULL_HIGH_VOL = "bull_high_vol"      # Strong but volatile
    BULL_LOW_VOL = "bull_low_vol"        # Steady growth
    BEAR_HIGH_VOL = "bear_high_vol"      # Declining volatility rising
    BEAR_LOW_VOL = "bear_low_vol"        # Stable decline
    SIDEWAYS = "sideways"                # Ranging market
    CRISIS = "crisis"                    # Market stress/crash
