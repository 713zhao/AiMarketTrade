"""
Trading system models - Pydantic v2 compatible models for virtual portfolio execution.

This module provides the data models for virtual trading, position tracking,
and portfolio management integrated with DeerflowState.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from enum import Enum


class TradeAction(str, Enum):
    """Trading action type."""
    BUY = "buy"
    SELL = "sell"


class ExecutedTrade(BaseModel):
    """Record of a single executed trade."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    trade_id: str = Field(description="Unique trade identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution time")
    ticker: str = Field(description="Security symbol")
    action: TradeAction = Field(description="BUY or SELL")
    quantity: int = Field(gt=0, description="Number of shares")
    price: float = Field(gt=0.0, description="Execution price")
    total_value: float = Field(gt=0.0, description="Quantity × Price")
    commission: float = Field(default=0.0, ge=0.0, description="Transaction commission")
    slippage: float = Field(default=0.0, ge=0.0, description="Price slippage cost")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Signal confidence")
    reason: Optional[str] = Field(None, description="Trade rationale")
    
    @property
    def net_value(self) -> float:
        """Total value including costs."""
        return self.total_value + self.commission + self.slippage if self.action == TradeAction.BUY else self.total_value - self.commission - self.slippage


class PortfolioPosition(BaseModel):
    """Current position in a security."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    ticker: str = Field(description="Security symbol")
    quantity: int = Field(ge=0, description="Number of shares")
    avg_cost: float = Field(ge=0.0, description="Average cost basis per share")
    current_price: float = Field(ge=0.0, description="Current market price")
    current_value: float = Field(ge=0.0, description="Quantity × Current Price")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last price update")
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized P&L on open position."""
        return self.current_value - (self.avg_cost * self.quantity)
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L percentage."""
        cost_basis = self.avg_cost * self.quantity
        if cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / cost_basis) * 100


class PortfolioMetrics(BaseModel):
    """Portfolio performance and risk metrics."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Value metrics
    total_value: float = Field(default=0.0, ge=0.0, description="Current portfolio value")
    cash: float = Field(default=0.0, ge=0.0, description="Available cash")
    invested_value: float = Field(default=0.0, ge=0.0, description="Value invested in securities")
    
    # P&L metrics
    realized_pnl: float = Field(default=0.0, description="P&L from closed trades")
    unrealized_pnl: float = Field(default=0.0, description="P&L from open positions")
    total_pnl: float = Field(default=0.0, description="Total P&L")
    
    # Return metrics
    initial_capital: float = Field(default=100000.0, gt=0.0, description="Starting capital")
    return_pct: float = Field(default=0.0, description="Total return percentage")
    annualized_return: float = Field(default=0.0, description="Annualized return %")
    
    # Risk metrics
    volatility: float = Field(default=0.0, ge=0.0, description="Portfolio volatility (annualized)")
    sharpe_ratio: float = Field(default=0.0, description="Risk-adjusted return")
    max_drawdown: float = Field(default=0.0, le=0.0, description="Maximum peak-to-trough decline")
    current_drawdown: float = Field(default=0.0, le=0.0, description="Current drawdown from peak")
    
    # Trading statistics
    total_trades: int = Field(default=0, ge=0, description="Number of trades executed")
    winning_trades: int = Field(default=0, ge=0, description="Number of winning trades")
    losing_trades: int = Field(default=0, ge=0, description="Number of losing trades")
    win_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="Winning trades %")
    avg_win: float = Field(default=0.0, description="Average winning trade")
    avg_loss: float = Field(default=0.0, description="Average losing trade")
    profit_factor: float = Field(default=0.0, ge=0.0, description="Total wins / total losses")
    
    # Time metrics
    days_active: int = Field(default=1, ge=1, description="Days portfolio has been active")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class TradingSession(BaseModel):
    """Virtual trading session state and history."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    session_id: str = Field(description="Unique session identifier")
    session_start: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    session_end: Optional[datetime] = Field(None, description="Session end time")
    
    # Session state
    starting_capital: float = Field(gt=0.0, description="Initial capital")
    current_capital: float = Field(default=0.0, ge=0.0, description="Current available capital")
    session_pnl: float = Field(default=0.0, description="Session P&L")
    session_return_pct: float = Field(default=0.0, description="Session return %")
    
    # Performance
    trades_executed: int = Field(default=0, ge=0, description="Trades in this session")
    session_trades: List[ExecutedTrade] = Field(default_factory=list, description="Trades executed")
    max_session_drawdown: float = Field(default=0.0, le=0.0, description="Session drawdown")
    
    # Status
    is_active: bool = Field(default=True, description="Is session active?")
    reason_closed: Optional[str] = Field(None, description="Why session ended")


class TradeRecommendation(BaseModel):
    """Recommendation to execute a trade based on analysis."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    ticker: str = Field(description="Security symbol")
    action: TradeAction = Field(description="BUY or SELL")
    confidence: float = Field(ge=0.0, le=1.0, description="Recommendation confidence")
    quantity: Optional[int] = Field(None, ge=0, description="Suggested quantity")
    target_price: Optional[float] = Field(None, gt=0.0, description="Target price")
    stop_loss: Optional[float] = Field(None, gt=0.0, description="Stop loss level")
    time_horizon: str = Field(default="MEDIUM", description="SHORT, MEDIUM, LONG")
    reasoning: str = Field(default="", description="Rationale for recommendation")
    source_node: str = Field(default="consensus", description="Which node generated this")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Creation time")


class PortfolioStats(BaseModel):
    """Aggregated portfolio statistics and analysis."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Composition
    num_holdings: int = Field(default=0, ge=0, description="Number of positions")
    sector_allocation: Dict[str, float] = Field(default_factory=dict, description="% by sector")
    top_holdings: List[tuple] = Field(default_factory=list, description="Top 5 positions")
    
    # Concentration
    largest_position_pct: float = Field(default=0.0, ge=0.0, le=100.0, description="Largest position %")
    herfindahl_index: float = Field(default=1.0, ge=0.0, le=1.0, description="Concentration metric")
    
    # Correlation
    avg_correlation: float = Field(default=0.5, ge=-1.0, le=1.0, description="Average pair correlation")
    
    # Risk profile
    portfolio_beta: float = Field(default=1.0, description="Market beta")
    portfolio_alpha: float = Field(default=0.0, description="Alpha vs benchmark")
    
    # Efficiency
    diversification_ratio: float = Field(default=1.0, gt=0.0, description="Portfolio vol / avg stock vol")
    information_ratio: float = Field(default=0.0, description="Alpha / tracking error")


class PositionDriftAnalysis(BaseModel):
    """Analysis of portfolio drift from target allocation."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    current_weights: Dict[str, float] = Field(default_factory=dict, description="Current %")
    target_weights: Dict[str, float] = Field(default_factory=dict, description="Target %")
    drift_amounts: Dict[str, float] = Field(default_factory=dict, description="Difference %")
    
    max_drift: float = Field(default=0.0, ge=0.0, description="Largest drift")
    max_drift_ticker: Optional[str] = Field(None, description="Which ticker drifted most")
    
    portfolio_drift: float = Field(default=0.0, ge=0.0, description="Overall drift amount")
    rebalancing_needed: bool = Field(default=False, description="Rebalancing required?")
    
    estimated_rebalance_trades: int = Field(default=0, ge=0, description="Trades needed")
    estimated_rebalance_cost: float = Field(default=0.0, ge=0.0, description="Rebalancing cost")


class VirtualExecutionRecord(BaseModel):
    """Record of trade execution in virtual environment."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    execution_id: str = Field(description="Unique execution ID")
    execution_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When executed")
    
    # Trade details
    ticker: str = Field(description="Security")
    action: TradeAction = Field(description="BUY or SELL")
    quantity: int = Field(gt=0, description="Shares")
    
    # Pricing
    intended_price: float = Field(gt=0.0, description="Price from recommendation")
    executed_price: float = Field(gt=0.0, description="Actual execution price")
    slippage_amount: float = Field(default=0.0, description="Price - intended_price")
    commission: float = Field(default=0.0, ge=0.0, description="Fee")
    
    # Portfolio impact
    portfolio_cash_before: float = Field(description="Cash before trade")
    portfolio_cash_after: float = Field(description="Cash after trade")
    portfolio_value_before: float = Field(description="Total value before")
    portfolio_value_after: float = Field(description="Total value after")
    
    # Status
    status: str = Field("EXECUTED", description="EXECUTED or REJECTED")
    rejection_reason: Optional[str] = Field(None, description="Why rejected")
    
    # Reference
    parent_recommendation_id: Optional[str] = Field(None, description="Which recommendation")
    session_id: str = Field(description="Trading session")
