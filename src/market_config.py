"""
Market configuration for multi-market trading system.
Defines supported markets and their associated tickers.
"""

from enum import Enum
from typing import Dict, List
from datetime import datetime

class Market(str, Enum):
    """Supported trading markets."""
    US = "US"
    CHINA = "CHINA"
    HONGKONG = "HONGKONG"

# Market-specific industry tickers
MARKET_INDUSTRY_TICKERS: Dict[Market, Dict[str, List[str]]] = {
    Market.US: {
        "AI": ["NVDA", "PLTR", "AI", "UPST", "NFLX", "GOOGL", "MSFT", "META"],
        "TECH": ["AAPL", "MSFT", "GOOGL", "TSLA", "META", "NVDA", "AMD", "INTEL"],
        "POWER": ["NEE", "DUK", "SO", "AEP", "EXC", "XEL", "ED"],
        "HEALTHCARE": ["JNJ", "PFE", "UNH", "LLY", "AZN", "ABBV"],
        "FINANCE": ["JPM", "BAC", "WFC", "GS", "MS", "BLK"],
        "ENERGY": ["XOM", "CVX", "COP", "MPC", "PSX"],
        "RETAIL": ["AMZN", "WMT", "TGT", "COST", "HD"],
        "TELECOM": ["VZ", "T", "TMUS", "S"],
    },
    Market.CHINA: {
        "AI": ["BIDU", "JD", "NTES", "TME", "BILIBILI"],
        "TECH": ["BIDU", "TME", "JD", "NTES", "BILIBILI", "ME"],
        "FINANCE": ["HUYA", "FUTU", "QFIN", "XRX"],
        "RETAIL": ["JD", "VIPS", "PDD"],
        "ENERGY": ["PES", "ENN"],
        "HEALTHCARE": ["CBPO", "CRSP", "MRNA"],
        "TELECOM": ["CHL", "CHU"],
    },
    Market.HONGKONG: {
        "AI": ["9988.HK", "3690.HK", "2018.HK", "9618.HK"],  # Alibaba, JD.com, Xiaomi, Bitauto
        "TECH": ["9988.HK", "3690.HK", "2018.HK", "1810.HK"],  # Tech related
        "FINANCE": ["2333.HK", "1398.HK", "6823.HK", "2601.HK"],  # Banking
        "RETAIL": ["3333.HK", "1888.HK", "2313.HK"],  # Retail
        "ENERGY": ["0883.HK", "2883.HK", "3337.HK"],  # Energy
        "HEALTHCARE": ["1177.HK", "1211.HK"],  # Healthcare
        "TELECOM": ["0941.HK", "2888.HK"],  # Telecom
    }
}

# Market-specific default tickers
MARKET_DEFAULT_TICKERS: Dict[Market, List[str]] = {
    Market.US: ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"],
    Market.CHINA: ["BIDU", "JD", "NTES", "TME"],
    Market.HONGKONG: ["9988.HK", "3690.HK", "2018.HK", "1810.HK"],
}

# Market trading hours (UTC)
MARKET_HOURS: Dict[Market, tuple] = {
    Market.US: (13, 21),  # NYSE: 9:30-16:00 EST (13:30-21:00 UTC)
    Market.CHINA: (0, 9),  # SSE: 9:30-15:00 CST (1:30-7:00 UTC)
    Market.HONGKONG: (1, 10),  # HKEx: 9:30-16:00 HKT (1:30-8:00 UTC)
}

def get_market_tickers(market: Market, industry: str = None) -> List[str]:
    """Get tickers for a market and optionally an industry."""
    if market not in MARKET_INDUSTRY_TICKERS:
        return []
    
    if industry is None:
        return MARKET_DEFAULT_TICKERS.get(market, [])
    
    return MARKET_INDUSTRY_TICKERS[market].get(industry.upper(), [])

def get_all_industries(market: Market) -> List[str]:
    """Get all available industries for a market."""
    if market not in MARKET_INDUSTRY_TICKERS:
        return []
    return list(MARKET_INDUSTRY_TICKERS[market].keys())

def is_market_open(market: Market) -> bool:
    """
    Check if a market is currently open.
    
    Args:
        market: Market to check
    
    Returns:
        True if market is open during current UTC hour, False otherwise
    """
    if market not in MARKET_HOURS:
        return False
    
    open_hour, close_hour = MARKET_HOURS[market]
    current_utc_hour = datetime.utcnow().hour
    
    # Handle markets that span midnight (e.g., CHINA: 0-9)
    if open_hour < close_hour:
        return open_hour <= current_utc_hour < close_hour
    else:
        # Wraps around midnight
        return current_utc_hour >= open_hour or current_utc_hour < close_hour
