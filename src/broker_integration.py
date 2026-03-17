"""
Phase 6: Broker API Integration & Live Trading

Nodes and adapters for connecting to brokers and executing live trades.

经纪商API集成和实时交易：连接到经纪商并执行实时交易的节点和适配器。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging

import numpy as np
from pydantic import BaseModel, Field

from .state import (
    DeerflowState,
    Order,
    BrokerAccount,
    BrokerPosition,
    Trade,
    BrokerAccountState,
    BrokerExecutionPlan,
    ComplianceRecord,
    TransactionExecutionPlan,
)
from .nodes.base import BaseNode, NodeResult


logger = logging.getLogger(__name__)


# ============================================================================
# BROKER ADAPTERS (Abstract & Implementations)
# ============================================================================

class BrokerAdapter(ABC):
    """
    Abstract broker adapter interface.
    
    所有经纪商适配器必须实现的接口。
    """
    
    def __init__(self, broker_id: str, account: BrokerAccount):
        self.broker_id = broker_id
        self.account = account
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to broker API."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close broker connection."""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Test connection and authentication."""
        pass
    
    @abstractmethod
    async def get_account_status(self) -> Dict[str, Any]:
        """Fetch current account state."""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[BrokerPosition]:
        """Fetch current holdings."""
        pass
    
    @abstractmethod
    async def submit_order(self, order: Order) -> str:
        """Submit order to broker. Return order_id."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order."""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get status of submitted order."""
        pass
    
    @abstractmethod
    async def get_filled_orders(self, limit: int = 100) -> List[Order]:
        """Get recent filled orders."""
        pass


class AlpacaAdapter(BrokerAdapter):
    """
    Alpaca broker integration (US equities, crypto, fractional shares).
    
    美国股票、加密货币和零碎股票的Alpaca经纪商集成。
    """
    
    async def connect(self) -> bool:
        """Connect to Alpaca API."""
        try:
            # In real implementation: import alpaca_trade_api and initialize
            # from alpaca_trade_api import REST, StreamConn
            # self.api = REST(api_key, secret_key, base_url=self.account.base_url)
            logger.info(f"Alpaca connection established to {self.account.base_url}")
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Alpaca connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Alpaca."""
        self.is_connected = False
        return True
    
    async def validate_connection(self) -> bool:
        """Verify Alpaca connection and authentication."""
        try:
            if not self.is_connected:
                return False
            # Real: self.api.get_account()
            logger.info(f"Alpaca account {self.account.account_id} validated")
            return True
        except Exception as e:
            logger.error(f"Alpaca validation failed: {e}")
            return False
    
    async def get_account_status(self) -> Dict[str, Any]:
        """Get Alpaca account details."""
        # Mock implementation
        return {
            "account_id": self.account.account_id,
            "cash": 100000.0,
            "buying_power": 200000.0,
            "portfolio_value": 500000.0,
            "total_value": 600000.0,
            "equity_percent": 0.85,
            "is_margin_call": False,
        }
    
    async def get_positions(self) -> List[BrokerPosition]:
        """Get Alpaca positions."""
        # Mock implementation
        positions = []
        
        # Example positions (mock data)
        for ticker, quantity in {"AAPL": 100, "MSFT": 50}.items():
            position = BrokerPosition(
                position_id=f"alpaca_{ticker}",
                broker_id="alpaca",
                ticker=ticker,
                quantity=quantity,
                avg_cost=150.0 if ticker == "AAPL" else 320.0,
                current_price=180.0 if ticker == "AAPL" else 350.0,
                market_value=quantity * (180.0 if ticker == "AAPL" else 350.0),
                unrealized_pnl=quantity * (30.0 if ticker == "AAPL" else 30.0),
                unrealized_pnl_pct=(30.0 / (150.0 if ticker == "AAPL" else 320.0)),
            )
            positions.append(position)
        
        return positions
    
    async def submit_order(self, order: Order) -> str:
        """Submit order to Alpaca."""
        # Mock implementation
        order_id = f"alpaca_{order.ticker}_{int(datetime.utcnow().timestamp() * 1000)}"
        logger.info(f"Alpaca order {order_id} submitted: {order.order_type} {order.quantity} {order.ticker}")
        return order_id
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel Alpaca order."""
        logger.info(f"Alpaca order {order_id} cancelled")
        return True
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Check Alpaca order status."""
        # Mock: return as if filled
        return {
            "order_id": order_id,
            "status": "filled",
            "filled_price": 180.0,
            "filled_quantity": 100,
        }
    
    async def get_filled_orders(self, limit: int = 100) -> List[Order]:
        """Get recent Alpaca fills."""
        # Mock implementation
        filled_orders = []
        
        order = Order(
            order_id=f"alpaca_order_mock",
            broker_id="alpaca",
            ticker="AAPL",
            order_type="BUY",
            execution_type="MARKET",
            quantity=100,
            status="FILLED",
            created_at=datetime.utcnow() - timedelta(hours=1),
            filled_at=datetime.utcnow(),
            filled_price=180.0,
            filled_quantity=100,
            commission=0.0,
        )
        filled_orders.append(order)
        
        return filled_orders


class InteractiveBrokersAdapter(BrokerAdapter):
    """
    Interactive Brokers integration (global, futures, options).
    
    全球市场、期货和期权的交互经纪商集成。
    """
    
    async def connect(self) -> bool:
        """Connect to Interactive Brokers."""
        try:
            # In real implementation: import ibapi
            logger.info(f"IB connection established for account {self.account.account_id}")
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"IB connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from IB."""
        self.is_connected = False
        return True
    
    async def validate_connection(self) -> bool:
        """Verify IB connection."""
        try:
            if not self.is_connected:
                return False
            logger.info(f"IB account {self.account.account_id} validated")
            return True
        except Exception as e:
            logger.error(f"IB validation failed: {e}")
            return False
    
    async def get_account_status(self) -> Dict[str, Any]:
        """Get IB account details."""
        # Mock implementation
        return {
            "account_id": self.account.account_id,
            "cash": 150000.0,
            "buying_power": 300000.0,
            "portfolio_value": 750000.0,
            "total_value": 900000.0,
            "equity_percent": 0.88,
            "is_margin_call": False,
        }
    
    async def get_positions(self) -> List[BrokerPosition]:
        """Get IB positions."""
        # Mock implementation: return empty for now
        return []
    
    async def submit_order(self, order: Order) -> str:
        """Submit order to IB."""
        order_id = f"ib_{order.ticker}_{int(datetime.utcnow().timestamp() * 1000)}"
        logger.info(f"IB order {order_id} submitted")
        return order_id
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel IB order."""
        logger.info(f"IB order {order_id} cancelled")
        return True
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Check IB order status."""
        return {
            "order_id": order_id,
            "status": "filled",
            "filled_price": 150.0,
            "filled_quantity": 100,
        }
    
    async def get_filled_orders(self, limit: int = 100) -> List[Order]:
        """Get recent IB fills."""
        return []


# ============================================================================
# PHASE 6: LIVE TRADING NODES
# ============================================================================

class BrokerConnectorNode(BaseNode):
    """
    Establish and maintain broker connections.
    
    与经纪商建立和维护连接。
    """
    
    node_type = "broker_connector"
    
    def __init__(self):
        super().__init__()
        self.adapters: Dict[str, BrokerAdapter] = {}
    
    async def execute(self, state: DeerflowState) -> NodeResult:
        """Connect to configured brokers."""
        try:
            # Initialize broker adapters
            for broker_id, account in state.broker_accounts.items():
                adapter = self._create_adapter(broker_id, account)
                
                if adapter:
                    # Try to connect
                    connected = await adapter.connect()
                    validated = await adapter.validate_connection() if connected else False
                    
                    if validated:
                        self.adapters[broker_id] = adapter
                        state.broker_connections[broker_id] = adapter
                        logger.info(f"✓ Broker {broker_id} connected and validated")
                    else:
                        logger.warning(f"✗ Broker {broker_id} validation failed")
            
            state.completed_nodes.append(self.node_type)
            
            return NodeResult(
                status="success" if self.adapters else "failed",
                message=f"Connected to {len(self.adapters)} brokers",
                data={"connected_brokers": list(self.adapters.keys())},
            )
        
        except Exception as e:
            state.add_error(self.node_type, str(e))
            return NodeResult(status="error", message=str(e), data={})
    
    def _create_adapter(self, broker_id: str, account: BrokerAccount) -> Optional[BrokerAdapter]:
        """Create appropriate broker adapter."""
        if broker_id == "alpaca":
            return AlpacaAdapter(broker_id, account)
        elif broker_id == "ib" or broker_id == "interactive_brokers":
            return InteractiveBrokersAdapter(broker_id, account)
        else:
            logger.warning(f"Unknown broker: {broker_id}")
            return None


class TradeExecutorNode(BaseNode):
    """
    Execute trades through broker APIs.
    
    通过经纪商API执行交易。
    """
    
    node_type = "trade_executor"
    
    async def execute(self, state: DeerflowState) -> NodeResult:
        """Execute trading plan through brokers."""
        try:
            if not state.broker_execution_plan:
                return NodeResult(
                    status="skipped",
                    message="No execution plan provided",
                    data={},
                )
            
            plan = state.broker_execution_plan
            broker_id = plan.broker_id
            
            # Get adapter
            if broker_id not in state.broker_connections:
                return NodeResult(
                    status="failed",
                    message=f"Broker {broker_id} not connected",
                    data={},
                )
            
            adapter = state.broker_connections[broker_id]
            
            # Submit each order
            for trade in plan.trades:
                try:
                    order_id = await adapter.submit_order(trade)
                    trade.order_id = order_id
                    trade.status = "SUBMITTED"
                    state.submitted_orders.append(trade)
                    logger.info(f"✓ Order {order_id} submitted")
                except Exception as e:
                    logger.error(f"✗ Order submission failed: {e}")
                    state.add_error(self.node_type, str(e), ticker=trade.ticker)
            
            plan.status = "IN_PROGRESS"
            plan.started_at = datetime.utcnow()
            state.completed_nodes.append(self.node_type)
            
            return NodeResult(
                status="success",
                message=f"Submitted {len(state.submitted_orders)} orders",
                data={"submitted_count": len(state.submitted_orders)},
            )
        
        except Exception as e:
            state.add_error(self.node_type, str(e))
            return NodeResult(status="error", message=str(e), data={})


class OrderMonitorNode(BaseNode):
    """
    Track pending orders and update status.
    
    跟踪待处理订单并更新状态。
    """
    
    node_type = "order_monitor"
    
    async def execute(self, state: DeerflowState) -> NodeResult:
        """Monitor order fills and updates."""
        try:
            filled_count = 0
            
            for order in state.submitted_orders:
                if order.status in ["FILLED", "CANCELLED"]:
                    continue
                
                broker_id = order.broker_id
                if broker_id not in state.broker_connections:
                    continue
                
                adapter = state.broker_connections[broker_id]
                
                # Check status
                status_info = await adapter.get_order_status(order.order_id)
                
                if status_info.get("status") == "filled":
                    order.status = "FILLED"
                    order.filled_price = status_info.get("filled_price", order.price)
                    order.filled_quantity = status_info.get("filled_quantity", order.quantity)
                    order.filled_at = datetime.utcnow()
                    filled_count += 1
                    logger.info(f"✓ Order {order.order_id} filled at {order.filled_price}")
                    
                    # Create Trade record
                    trade = Trade(
                        trade_id=f"trade_{order.order_id}",
                        broker_id=order.broker_id,
                        ticker=order.ticker,
                        entry_order_id=order.order_id,
                        entry_price=order.filled_price,
                        quantity=order.filled_quantity,
                        entry_time=order.filled_at,
                        entry_commission=order.commission,
                    )
                    state.filled_trades.append(trade)
                    
                    # Move to filled trades
                    state.pending_orders.append(order)
                
                elif status_info.get("status") == "partial":
                    order.status = "PARTIAL"
                    order.filled_quantity = status_info.get("filled_quantity", 0)
                    logger.info(f"◐ Order {order.order_id} partially filled: {order.filled_quantity}/{order.quantity}")
            
            state.completed_nodes.append(self.node_type)
            
            return NodeResult(
                status="success",
                message=f"Monitored {len(state.submitted_orders)} orders, {filled_count} filled",
                data={"filled_count": filled_count},
            )
        
        except Exception as e:
            state.add_error(self.node_type, str(e))
            return NodeResult(status="error", message=str(e), data={})


class PositionManagerNode(BaseNode):
    """
    Manage and rebalance live positions.
    
    管理和重新平衡实时持仓。
    """
    
    node_type = "position_manager"
    
    async def execute(self, state: DeerflowState) -> NodeResult:
        """Update positions from brokers."""
        try:
            total_positions = 0
            
            for broker_id, adapter in state.broker_connections.items():
                # Fetch positions
                positions = await adapter.get_positions()
                total_positions += len(positions)
                
                for position in positions:
                    state.broker_account_states[broker_id].open_positions.append(position)
                    logger.info(f"✓ Position: {position.ticker} x{position.quantity} @ ${position.current_price}")
            
            # Calculate deltas vs target
            if state.portfolio_snapshot and state.broker_account_states:
                target_positions = state.portfolio_snapshot.target_positions
                current = {}
                
                for account_state in state.broker_account_states.values():
                    for position in account_state.open_positions:
                        current[position.ticker] = current.get(position.ticker, 0) + position.quantity
                
                # Identify needed rebalancing
                deltas = {}
                for ticker, target_qty in target_positions.items():
                    current_qty = current.get(ticker, 0)
                    deltas[ticker] = target_qty - current_qty
                
                state.broker_account_states[list(state.broker_account_states.keys())[0]].position_deltas = deltas
            
            state.completed_nodes.append(self.node_type)
            
            return NodeResult(
                status="success",
                message=f"Updated {total_positions} positions",
                data={"position_count": total_positions},
            )
        
        except Exception as e:
            state.add_error(self.node_type, str(e))
            return NodeResult(status="error", message=str(e), data={})


class AccountMonitorNode(BaseNode):
    """
    Track real-time account metrics (cash, buying power, P&L).
    
    跟踪实时账户指标。
    """
    
    node_type = "account_monitor"
    
    async def execute(self, state: DeerflowState) -> NodeResult:
        """Monitor account status across brokers."""
        try:
            for broker_id, adapter in state.broker_connections.items():
                # Get account status
                account_info = await adapter.get_account_status()
                
                # Create account state
                account_state = BrokerAccountState(
                    account_id=account_info.get("account_id", ""),
                    broker_id=broker_id,
                    cash=account_info.get("cash", 0.0),
                    buying_power=account_info.get("buying_power", 0.0),
                    total_value=account_info.get("total_value", 0.0),
                    portfolio_value=account_info.get("portfolio_value", 0.0),
                    equity_percent=account_info.get("equity_percent", 1.0),
                    is_margin_call=account_info.get("is_margin_call", False),
                )
                
                state.broker_account_states[broker_id] = account_state
                logger.info(f"✓ {broker_id}: ${account_state.total_value:.0f} equity, ${account_state.cash:.0f} cash")
            
            state.completed_nodes.append(self.node_type)
            
            return NodeResult(
                status="success",
                message=f"Updated {len(state.broker_account_states)} accounts",
                data={"account_count": len(state.broker_account_states)},
            )
        
        except Exception as e:
            state.add_error(self.node_type, str(e))
            return NodeResult(status="error", message=str(e), data={})


class RiskControlNode(BaseNode):
    """
    Pre-trade validation and circuit breakers.
    
    交易前验证和熔断机制。
    """
    
    node_type = "risk_control"
    
    def __init__(self):
        super().__init__()
        self.max_position_size_pct = 0.10  # Max 10% of portfolio per position
        self.max_daily_loss_pct = -0.02     # Max -2% daily loss
        self.sector_concentration_limit = 0.30  # Max 30% in one sector
    
    async def execute(self, state: DeerflowState) -> NodeResult:
        """Validate trades against risk limits."""
        try:
            if not state.broker_execution_plan:
                return NodeResult(status="skipped", message="No execution plan", data={})
            
            plan = state.broker_execution_plan
            violations = []
            
            if not state.broker_account_states:
                return NodeResult(status="skipped", message="No account data", data={})
            
            total_portfolio_value = sum(acc.total_value for acc in state.broker_account_states.values())
            
            # Check position sizes
            for trade in plan.trades:
                trade_cost = trade.quantity * (trade.price or 100.0)  # Estimate cost
                position_pct = trade_cost / total_portfolio_value if total_portfolio_value > 0 else 0
                
                if position_pct > self.max_position_size_pct:
                    violations.append(f"{trade.ticker}: {position_pct:.1%} exceeds {self.max_position_size_pct:.1%} limit")
                    logger.warning(f"⚠ Position size limit exceeded: {trade.ticker}")
            
            # Check daily loss
            total_daily_pnl = sum(
                (acc.unrealized_day_pnl + acc.realized_day_pnl)
                for acc in state.broker_account_states.values()
            )
            daily_loss_pct = total_daily_pnl / total_portfolio_value if total_portfolio_value > 0 else 0
            
            if daily_loss_pct < self.max_daily_loss_pct:
                violations.append(f"Daily loss {daily_loss_pct:.2%} exceeds limit {self.max_daily_loss_pct:.2%}")
                state.circuit_breaker_active = True
                state.circuit_breaker_reason = f"Daily loss limit: {daily_loss_pct:.2%}"
            
            # Summary
            if violations:
                logger.warning(f"⚠ Risk violations detected: {len(violations)}")
                for v in violations:
                    logger.warning(f"  - {v}")
            
            state.last_validation = datetime.utcnow()
            state.completed_nodes.append(self.node_type)
            
            return NodeResult(
                status="success" if not violations else "warning",
                message=f"Validation complete, {len(violations)} violations",
                data={"violations": violations, "circuit_breaker_active": state.circuit_breaker_active},
            )
        
        except Exception as e:
            state.add_error(self.node_type, str(e))
            return NodeResult(status="error", message=str(e), data={})


class ComplianceLoggerNode(BaseNode):
    """
    Log all trades for compliance and audit trails.
    
    为合规和审计目的记录所有交易。
    """
    
    node_type = "compliance_logger"
    
    async def execute(self, state: DeerflowState) -> NodeResult:
        """Log all executed trades for compliance."""
        try:
            log_count = 0
            
            # Log filled trades
            for trade in state.filled_trades:
                record = ComplianceRecord(
                    record_id=f"trade_{trade.trade_id}",
                    record_type="TRADE_EXECUTED",
                    broker_id=trade.broker_id,
                    account_id="",
                    ticker=trade.ticker,
                    trade_id=trade.trade_id,
                    quantity=trade.quantity,
                    price=trade.entry_price,
                    commission=trade.entry_commission,
                    description=f"Trade executed: BUY {trade.quantity} {trade.ticker} @ ${trade.entry_price}",
                )
                state.compliance_records.append(record)
                log_count += 1
            
            # Log account status snapshots
            for broker_id, account_state in state.broker_account_states.items():
                record = ComplianceRecord(
                    record_id=f"account_{broker_id}_{int(datetime.utcnow().timestamp())}",
                    record_type="ACCOUNT_SNAPSHOT",
                    broker_id=broker_id,
                    account_id=account_state.account_id,
                    account_value_after=account_state.total_value,
                    cash_after=account_state.cash,
                    description=f"Account snapshot: ${account_state.total_value} equity, ${account_state.cash} cash",
                )
                state.compliance_records.append(record)
                log_count += 1
            
            logger.info(f"✓ {log_count} compliance records logged")
            state.completed_nodes.append(self.node_type)
            
            return NodeResult(
                status="success",
                message=f"Logged {log_count} compliance records",
                data={"log_count": log_count},
            )
        
        except Exception as e:
            state.add_error(self.node_type, str(e))
            return NodeResult(status="error", message=str(e), data={})


__all__ = [
    "BrokerAdapter",
    "AlpacaAdapter",
    "InteractiveBrokersAdapter",
    "BrokerConnectorNode",
    "TradeExecutorNode",
    "OrderMonitorNode",
    "PositionManagerNode",
    "AccountMonitorNode",
    "RiskControlNode",
    "ComplianceLoggerNode",
]
