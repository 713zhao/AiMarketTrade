# Phase 6: Broker API Integration & Live Trading

**Status**: 🚀 In Development  
**Target Lines**: ~2,500 lines (nodes + state models + broker connectors)  
**Timeline**: Current phase  

---

## Executive Summary

Phase 6 extends Phase 5's production capabilities with live broker integration and order execution. The system transitions from backtesting/analysis to actual market participation with real capital deployment through broker APIs (Alpaca, Interactive Brokers, etc.).

### Phase 6 Objectives

1. **Broker API Connectivity** - Unified interface to multiple brokers
2. **Order Execution** - Market, limit, stop-loss, and conditional orders
3. **Position Management** - Track, update, and rebalance live positions
4. **Account Monitoring** - Real-time portfolio performance and risk metrics
5. **Trade Logging** - Compliance and audit trails for all executions
6. **Risk Controls** - Pre-trade validation and circuit breakers

---

## Architecture Overview

### Component Hierarchy

```
                    Live Trading Manager
                             |
                  +----------+----------+
                  |                     |
            Broker Connector      Trade Executor
                  |                     |
      +-----+-----+-----+      +---+----+----+
      |     |     |     |      |   |    |    |
   Alpaca  IB  E*TRADE Crypto  BuySell Limit Stop Portfolio
                            
                    Order Monitor
                             |
            +--------+-------+-------+
            |        |       |       |
         Position  Account  P&L   Compliance
         Manager   Monitor  Track  Logger
```

### Data Flow

```
Phase 5 Strategy
  |
  v
Execute Trade Decision
  |
  v
Validate Trade Against Limits
  |
  v
Select Broker & Order Type
  |
  v
Submit Order (Create/Modify/Cancel)
  |
  v
Monitor Order Status
  |
  v
Update Position & Track P&L
  |
  v
Log for Compliance
```

---

## New State Models

### 1. BrokerCredentials
**Purpose**: Secure broker authentication details.

```python
class BrokerAccount(BaseModel):
    broker_id: str              # Broker identifier (alpaca, ib, etc)
    account_id: str             # Broker account number
    account_name: str           # Display name
    is_live: bool               # Paper or live trading
    api_key: str                # Encrypted API key (stored in env)
    api_secret: str             # Encrypted secret (stored in env)
    base_url: str               # API endpoint
    max_daily_loss: float       # Max loss limit per day
    max_position_size: float    # Max capital per position
    max_leverage: float         # Max leverage allowed
```

### 2. Order
**Purpose**: Pending or filled order details.

```python
class Order(BaseModel):
    order_id: str               # Unique order ID
    broker_id: str              # Which broker
    ticker: str                 # Security symbol
    order_type: str             # BUY, SELL, SHORT, COVER
    execution_type: str         # MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP
    quantity: int               # Shares/contracts
    price: Optional[float]      # Limit price (if applicable)
    stop_price: Optional[float] # Stop price (if applicable)
    status: str                 # PENDING, SUBMITTED, FILLED, PARTIAL, CANCELLED, REJECTED
    created_at: datetime        # Creation timestamp
    filled_at: Optional[datetime]  # Execution timestamp
    filled_price: Optional[float]  # Actual execution price
    filled_quantity: int        # Filled shares
    commission: float           # Transaction cost
    reason: str                 # Cancellation/rejection reason
```

### 3. Position
**Purpose**: Active holdings in broker account.

```python
class BrokerPosition(BaseModel):
    position_id: str            # Unique position ID
    broker_id: str              # Which broker
    ticker: str                 # Security symbol
    quantity: int               # Current shares
    avg_cost: float             # Average entry price
    current_price: float        # Last market price
    market_value: float         # Position value (quantity × current_price)
    unrealized_pnl: float       # Open P&L
    realized_pnl: float         # Closed P&L
    unrealized_pnl_pct: float   # P&L percentage
    updated_at: datetime        # Last update
```

### 4. Trade
**Purpose**: Completed trades (buy/sell pairs).

```python
class Trade(BaseModel):
    trade_id: str               # Unique trade ID
    broker_id: str              # Which broker
    ticker: str                 # Security
    entry_order_id: str         # Opens the trade
    exit_order_id: Optional[str]   # Closes the trade (None if open)
    entry_price: float          # Entry execution price
    exit_price: Optional[float]  # Exit price (None if still open)
    quantity: int               # Shares
    entry_time: datetime        # Entry timestamp
    exit_time: Optional[datetime]  # Exit timestamp  
    duration_seconds: Optional[int]   # Trade duration
    gross_pnl: float            # P&L before costs
    net_pnl: float              # P&L after commissions
    entry_commission: float     # Buy commission
    exit_commission: float      # Sell commission
    status: str                 # OPEN, CLOSED, PARTIAL
    notes: str                  # Entry reason, exit reason
```

### 5. BrokerAccount State
**Purpose**: Real-time broker account status.

```python
class BrokerAccountState(BaseModel):
    account_id: str              # Broker account ID
    broker_id: str               # Broker identifier
    timestamp: datetime          # As of timestamp
    cash: float                  # Available cash
    buying_power: float          # Cash × (1 + leverage)
    total_value: float           # Cash + portfolio value
    portfolio_value: float       # Position values sum
    day_trading_power: float     # Remaining day trade power
    maintenance_requirement: float  # Collateral needed
    maintenance_excess: float    # Excess collateral
    equity_percent: float        # Equity as % of total (inverse leverage)
    is_margin_call: bool         # Margin call flag
    last_checked: datetime       # Last API check
    unrealized_day_pnl: float    # Today's P&L
    realized_day_pnl: float      # Today's realized P&L
    realized_mtd_pnl: float      # Month-to-date realized
    open_positions: List[BrokerPosition]
    pending_orders: List[Order]
    recent_trades: List[Trade]
```

### 6. ExecutionPlan Extension
**Purpose**: Execution plan with broker routing (extends Phase 5).

```python
class BrokerExecutionPlan(BaseModel):
    execution_id: str            # Unique execution ID
    plan_id: str                 # From Phase 5 TransactionExecutionPlan
    broker_id: str               # Selected broker
    account_id: str              # Selected account
    trades: List[Order]          # Orders to execute
    total_commission: float      # Expected total cost
    execution_priority: str      # IMMEDIATE, AGGRESSIVE, PATIENT, VWAP, TWAP
    max_slippage_bps: float      # Max slippage tolerance
    time_limit_minutes: int      # Max time to execute all
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str                  # PLANNED, IN_PROGRESS, COMPLETED, FAILED, CANCELLED
    filled_orders: List[Order]
    execution_summary: str       # Narrative of execution
```

---

## New Nodes (7 total)

### 1. BrokerConnectorNode
**Purpose**: Establishes and maintains broker connections.

**Input**: `broker_credentials` from state  
**Output**: `broker_connections` (active connection handles)

```python
Responsibilities:
- Initialize broker API clients (Alpaca, IB, etc)
- Authenticate with broker
- Verify account permissions
- Test connectivity
- Handle disconnections/reconnects
```

### 2. TradeExecutorNode
**Purpose**: Execute trades through broker APIs.

**Input**: `execution_plan`, `broker_connections`  
**Output**: `submitted_orders` list with order IDs

```python
Responsibilities:
- Validate trades against account limits
- Select broker and order type
- Submit to broker API
- Handle rate limiting
- Log order submission
- Return order confirmations
```

### 3. OrderMonitorNode
**Purpose**: Track pending orders and updates.

**Input**: `submitted_orders`, `broker_connections`  
**Output**: `order_updates`, `filled_trades`

```python
Responsibilities:
- Poll broker for order status
- Handle order fills
- Detect partial fills
- Handle cancellations/rejections
- Update order details
- Track execution prices and commissions
```

### 4. PositionManagerNode
**Purpose**: Manage active positions and rebalancing.

**Input**: `broker_connections`, `portfolio_snapshot`  
**Output**: `current_positions`, `position_deltas`

```python
Responsibilities:
- Fetch current positions from broker
- Calculate position deltas vs target
- Identify rebalancing needs
- Generate rebalancing orders
- Track average costs and P&L
- Flag drift scenarios
```

### 5. AccountMonitorNode
**Purpose**: Track real-time account metrics.

**Input**: `broker_connections`  
**Output**: `broker_account_state`

```python
Responsibilities:
- Fetch account cash balance
- Calculate buying power
- Track maintenance requirement
- Detect margin calls
- Calculate daily P&L
- Monitor portfolio value
- Flag Account alerts
```

### 6. RiskControlNode
**Purpose**: Pre-trade validation and circuit breakers.

**Input**: `execution_plan`, `broker_account_state`, `current_positions`  
**Output**: `trade_validation_result`, optional `circuit_breaker_halt`

```python
Responsibilities:
- Validate position size limits
- Check daily loss limits
- Verify buying power
- Enforce sector concentration limits
- Check correlation with open positions
- Calculate portfolio impact
- Return approve/reject with reasons
```

### 7. ComplianceLoggerNode
**Purpose**: Log all trades for audit compliance.

**Input**: `filled_trades`, `order_updates`, `executed_trades`  
**Output**: `compliance_records`

```python
Responsibilities:
- Log all orders submitted
- Log all fills and executions
- Timestamp all events
- Record account state snapshots
- Generate compliance reports
- Archive for regulatory periods
- Flag suspicious activity
```

---

## Graph Topology (Phases 1-6)

```
                    [Input: Tickers]
                           |
            [Phase 1-2: Analysis]
     [6 Analysts + Consensus Decision]
                           |
           [Phase 3: Portfolio Optimization]
                           |
       [Phase 4: Multi-Scenario Analysis]
                           |
         [Phase 5: Efficient Frontier]
         [Backtest + Attribution]
                           |
      [Phase 6: Broker Integration]
              |
    [BrokerConnector] ──> [Check Connectivity]
              |
    [RiskControl] ──> [Validate Trades]
              |
   [TradeExecutor] ──> [Submit Orders]
              |
   [OrderMonitor] ──┬──> [Track Status]
              |    |
   [PositionManager]─┘
              |
   [AccountMonitor] ──> [Real-time Metrics]
              |
   [ComplianceLogger] ──> [Audit Trail]
              |
           [Output]
```

---

## Implementation Plan

### Step 1: State Models (450 lines)
- BrokerAccount validation
- Order management  
- Position tracking
- Trade recording
- Account monitoring
- Execution plan extension

### Step 2: Broker Adapter (600 lines)
- Abstract BrokerBase class
- Alpaca adapter
- Interactive Brokers adapter
- Order submission/cancellation
- Position fetching
- Account status

### Step 3: Nodes (1,200 lines)
- BrokerConnectorNode (150)
- TradeExecutorNode (200)
- OrderMonitorNode (200)
- PositionManagerNode (200)
- AccountMonitorNode (150)
- RiskControlNode (200)
- ComplianceLoggerNode (100)

### Step 4: Graph Updates (200 lines)
- Integrate Phase 6 with Phase 1-5
- Create execution pipeline
- Update state flow

### Step 5: Tests (800 lines)
- Unit tests for each node
- Integration tests with brokers
- Risk control validations
- Compliance logging tests

### Step 6: Documentation (300 lines)
- Phase 6 completion report
- Broker setup guides
- Live trading runbook

---

## Key Features

### 1. Multi-Broker Support
- Alpaca (equities, crypto, fractional)
- Interactive Brokers (global, futures, options)
- Robinhood (user retail)
- Extensible for additional brokers

### 2. Advanced Order Types
- Market orders
- Limit orders
- Stop-loss orders
- Trailing stop orders
- Conditional orders (if-then)
- VWAP/TWAP algorithms

### 3. Risk Management
- Position size limits
- Daily loss limits
- Sector concentration limits
- Correlation checks
- Buying power validation

### 4. Real-Time Monitoring
- Live position updates
- Account equity tracking
- P&L calculations
- Margin requirement monitoring
- Circuit breaker triggers

### 5. Compliance
- Complete audit trails
- Order timestamps
- Execution prices
- Commission tracking
- Trade reporting (Form 4 ready)

### 6. Error Handling
- Connection retry logic
- Order rejection handling
- Rate limit management
- Graceful degeneracy
- Fallback brokers

---

## Testing Strategy

### Unit Tests (150 tests)
- Broker adapter mock tests
- Order validation tests
- Position calculation tests
- Risk control threshold tests
- Compliance formatting tests

### Integration Tests (50 tests)
- Full order lifecycle (pending → filled)
- Position updates across brokers
- Account monitoring accuracy
- Multi-order execution
- Rebalancing scenarios

### End-to-End Tests (20 tests)
- Small portfolio execution
- Sector hedging
- Growth portfolio with stops
- Real-time monitoring
- Margin call simulation

---

## Success Criteria

### Functional
- ✅ Connect to 2+ brokers successfully
- ✅ Execute 100% of orders without errors
- ✅ Track positions with <100ms latency
- ✅ Enforce all risk controls
- ✅ Log all trades for compliance

### Performance
- < 1 second order submission
- < 500ms position fetch
- < 2 second account update
- < 100ms order status check

### Reliability
- 99.9% uptime for monitoring
- Auto-reconnection on disconnect
- Graceful degradation on API failures
- No lost orders or positions

### Compliance
- Complete audit log for all trades
- Timestamp accuracy ±1 second
- Commission tracking to 1 cent
- Trade reporting ready for regulators

---

## Deployment Checklist

- [ ] Set up broker accounts (paper trading first)
- [ ] Configure API credentials in .env
- [ ] Test broker connectivity
- [ ] Validate all risk limits
- [ ] Run compliance report generation
- [ ] Execute test trades on paper
- [ ] Monitor for 24 hours before live
- [ ] Enable circuit breakers
- [ ] Create runbook for on-call support

---

## Next Phases (Future)

### Phase 7: Advanced Strategies
- Options trading (calls, puts, spreads)
- Futures trading (ES, NQ, YM)
- Crypto derivatives
- Hedging strategies
- Pair trading

### Phase 8: Machine Learning
- Model portfolio optimization
- Trade timing prediction
- Market regime detection
- Volatility forecasting
- Order flow analysis

### Phase 9: Global Expansion
- Multi-currency trading
- International equities
- Forex markets
- Emerging markets integration
- Tax optimization

---

## Conclusion

Phase 6 bridges the gap between sophisticated analysis (Phases 1-5) and actual market participation. With broker integration, order execution, position management, and risk controls, the system becomes a production-grade trading platform capable of deploying capital with institutional-grade risk management and compliance logging.

