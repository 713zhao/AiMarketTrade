"""
Broker API integration models (Phase 6).

Broker accounts, orders, positions, execution tracking, and compliance auditing.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


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


__all__ = [
    "BrokerAccount",
    "Order",
    "BrokerPosition",
    "Trade",
    "BrokerAccountState",
    "BrokerExecutionPlan",
    "ComplianceRecord",
]
