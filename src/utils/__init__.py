"""
Utility functions for the deerflow trading system.

This package contains reusable helper functions organized by domain:
- analysis_utils: Technical indicator and analysis calculations
- portfolio_utils: Portfolio optimization and risk calculations
- broker_utils: Order validation and position calculations
- backtest_utils: Performance metrics and attribution calculations
"""

__all__ = [
    # Analysis utilities
    "calculate_rsi",
    "calculate_bollinger_bands",
    "calculate_macd",
    # Portfolio utilities
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_portfolio_volatility",
    "efficient_frontier",
    # Broker utilities
    "validate_order",
    "calculate_position_value",
    # Backtest utilities
    "calculate_returns",
    "calculate_drawdown",
    "calculate_performance_metrics",
]


# Analysis Utilities
def calculate_rsi(prices, period: int = 14) -> float:
    """Calculate Relative Strength Index."""
    deltas = prices.diff()
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi_values = 100.0 - (100.0 / (1.0 + rs))
    return float(rsi_values.iloc[-1])


def calculate_bollinger_bands(prices, period: int = 20, std_dev: float = 2.0):
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    return {
        "upper": float(upper_band.iloc[-1]),
        "middle": float(sma.iloc[-1]),
        "lower": float(lower_band.iloc[-1])
    }


def calculate_macd(prices, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD (Moving Average Convergence Divergence)."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line
    return {
        "macd": float(macd.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1])
    }


# Portfolio Utilities
def calculate_sharpe_ratio(returns, risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe Ratio."""
    excess_returns = returns - (risk_free_rate / 252)
    if excess_returns.std() == 0:
        return 0.0
    return float((excess_returns.mean() / excess_returns.std()) * (252 ** 0.5))


def calculate_sortino_ratio(returns, risk_free_rate: float = 0.02, target_return: float = 0.0) -> float:
    """Calculate Sortino Ratio (downside risk adjusted)."""
    excess_returns = returns - target_return
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std()
    if downside_std == 0:
        return 0.0
    return float(((returns.mean() - risk_free_rate) / downside_std) * (252 ** 0.5))


def calculate_portfolio_volatility(returns) -> float:
    """Calculate annualized portfolio volatility."""
    return float(returns.std() * (252 ** 0.5))


def efficient_frontier(expected_returns, cov_matrix, num_portfolios: int = 100):
    """Generate efficient frontier portfolios."""
    import numpy as np
    results = []
    num_assets = len(expected_returns)
    
    for _ in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        
        portfolio_return = np.sum(expected_returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = portfolio_return / portfolio_volatility if portfolio_volatility != 0 else 0
        
        results.append({
            "weights": weights.tolist(),
            "return": float(portfolio_return),
            "volatility": float(portfolio_volatility),
            "sharpe": float(sharpe)
        })
    
    return results


# Broker Utilities
def validate_order(order_dict: dict) -> bool:
    """Validate order parameters."""
    required_fields = ["ticker", "quantity", "order_type"]
    return all(field in order_dict for field in required_fields)


def calculate_position_value(quantity: float, current_price: float) -> float:
    """Calculate current position value."""
    return quantity * current_price


# Backtest Utilities
def calculate_returns(prices):
    """Calculate daily returns."""
    return prices.pct_change().dropna()


def calculate_drawdown(prices) -> dict:
    """Calculate drawdown metrics."""
    cumulative_returns = (1 + calculate_returns(prices)).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    return {
        "current": float(drawdown.iloc[-1]),
        "maximum": float(drawdown.min()),
        "duration": int((drawdown < 0).sum())
    }


def calculate_performance_metrics(returns, risk_free_rate: float = 0.02) -> dict:
    """Calculate comprehensive performance metrics."""
    return {
        "total_return": float(((1 + returns).prod() - 1)),
        "annual_return": float(returns.mean() * 252),
        "volatility": float(returns.std() * (252 ** 0.5)),
        "sharpe_ratio": calculate_sharpe_ratio(returns, risk_free_rate),
        "sortino_ratio": calculate_sortino_ratio(returns, risk_free_rate),
        "max_drawdown": calculate_drawdown(prices=(1 + returns).cumprod())["maximum"],
        "win_rate": float((returns > 0).sum() / len(returns)) if len(returns) > 0 else 0.0,
    }
