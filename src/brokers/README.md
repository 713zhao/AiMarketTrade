# Brokers Package - Deerflow Trading System

## Overview

The `brokers` package handles integration with real-world trading brokers and execution of live trades. It follows the **Adapter Pattern** to abstract different broker APIs behind a unified interface.

**Design Principle:** Decouple the trading system from specific broker implementations, making it easy to add new brokers without changing core logic.

---

## Architecture

```
src/brokers/
├── adapters.py                # Abstract adapter + broker implementations
├── nodes.py                   # Trading execution nodes
└── __init__.py                # Public API exports
```

---

## Core Architecture: The Adapter Pattern

```
┌──────────────────────────────────────────────────────────┐
│            Deerflow Trading System                        │
│  (Uses unified BrokerAdapter interface)                   │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │ BrokerAdapter  │ (Abstract)
        │  (Interface)   │
        └────┬───────────┘
             │
      ┌──────┴──────┬──────────────────┐
      ▼             ▼                   ▼
  ┌─────────┐  ┌──────────────┐   ┌─────────────┐
  │ Alpaca  │  │ Interactive  │   │ Future:     │
  │ Adapter │  │ Brokers      │   │ • TD Direct │
  │         │  │ Adapter      │   │ • Robinhood │
  └─────────┘  └──────────────┘   │ • etc.      │
                                   └─────────────┘
```

---

## Module 1: adapters.py

**Purpose:** Define broker adapter interface and implementations

### Abstract Base Class: BrokerAdapter

```python
class BrokerAdapter(ABC):
    """Abstract interface all brokers must implement."""
    
    # Connection methods
    async def connect(self) -> bool
    async def disconnect(self) -> bool
    async def validate_connection(self) -> bool
    
    # Account methods
    async def get_account_status(self) -> Dict[str, Any]
    async def get_positions(self) -> List[BrokerPosition]
    async def get_balance(self) -> float
    
    # Order methods
    async def submit_order(self, order: Order) -> str  # Returns order_id
    async def cancel_order(self, order_id: str) -> bool
    async def get_order_status(self, order_id: str) -> str
    
    # Trade methods
    async def get_completed_trades(self, since: datetime) -> List[Trade]
    async def get_trade_details(self, trade_id: str) -> Trade
```

### Implementation 1: AlpacaAdapter

**Broker:** Alpaca (Stock trading, no margin)

**Features:**
- Limited to US stock trading hours (9:30 AM - 4:00 PM ET)
- Pre-market/after-market sessions available
- Paper trading mode for testing
- Real-time market data included

**Key Methods:**

```python
class AlpacaAdapter(BrokerAdapter):
    """Implementation for Alpaca broker."""
    
    async def connect(self) -> bool:
        """Establish connection using API key/secret."""
        # Uses alpaca-trade-api library
        pass
    
    async def submit_order(self, order: Order) -> str:
        """Submit market/limit/stop orders."""
        # Types: buy/sell, market/limit/stop
        pass
    
    async def get_positions(self) -> List[BrokerPosition]:
        """Fetch current holdings."""
        # Qty, entry price, current price, unrealized P&L
        pass
```

**Limitations:**
- ❌ No options trading
- ❌ No futures
- ✅ Fractional shares
- ✅ Paper trading mode

---

### Implementation 2: InteractiveBrokersAdapter

**Broker:** Interactive Brokers (Stocks, options, futures, crypto)

**Features:**
- Multiple asset classes (stocks, options, futures, forex, crypto)
- Margin trading available
- Complex order types supported
- Lower commissions but higher account minimums

**Key Methods:**

```python
class InteractiveBrokersAdapter(BrokerAdapter):
    """Implementation for Interactive Brokers."""
    
    async def connect(self) -> bool:
        """Establish TWS/Gateway connection."""
        # Requires IB Gateway or TWS running
        pass
    
    async def submit_order(self, order: Order) -> str:
        """Support complex order types."""
        # Market, limit, stop, trailing-stop, bracket orders
        # Conditional orders, algorithmic orders
        pass
    
    async def get_positions(self) -> List[BrokerPosition]:
        """Fetch positions across multiple accounts."""
        # Accounts, sub-accounts, portfolio values
        pass
```

**Advantages:**
- ✅ Options trading
- ✅ Futures trading
- ✅ Forex and crypto
- ✅ Block trading (large orders)
- ✅ Algorithmic order algorithms

---

## Module 2: nodes.py

**Purpose:** LangGraph nodes that execute trades using broker adapters

### Node Overview

| Node | Purpose | Input | Output |
|------|---------|-------|--------|
| `BrokerConnectorNode` | Establish broker connections | Credentials | Connected adapters |
| `TradeExecutorNode` | Submit orders to brokers | ExecutionPlan | Submitted orders |
| `OrderMonitorNode` | Track pending order status | Submitted orders | Status updates |
| `PositionManagerNode` | Monitor holdings | Orders | Position updates |
| `AccountMonitorNode` | Track account metrics | Positions | Account status |
| `RiskControlNode` | Enforce risk limits | Positions + state | Position adjustments |
| `ComplianceLoggerNode` | Audit trail | All trades | Compliance records |

---

### Node 1: BrokerConnectorNode

**Purpose:** Initialize and validate broker connections at system start

**Logic:**
```
For each configured broker:
  1. Create appropriate adapter (Alpaca/IB/etc)
  2. Call connect() - establish connection
  3. Call validate_connection() - test authentication
  4. Store adapter in state if successful
  5. Log connection status
```

**Implementation:**

```python
class BrokerConnectorNode(BaseNode):
    async def _execute(self, state: DeerflowState) -> DeerflowState:
        # For each broker in config
        for broker_id, account in state.broker_accounts.items():
            # Create adapter
            adapter = self._create_adapter(broker_id, account)
            
            # Connect
            if await adapter.connect():
                # Validate
                if await adapter.validate_connection():
                    state.broker_connections[broker_id] = adapter
                    state.add_status(f"Connected to {broker_id}")
        
        return state
```

**Execution:**
- **When:** At graph initialization
- **Frequency:** Once per session
- **Error Behavior:** If connection fails, system can continue with other brokers

---

### Node 2: TradeExecutorNode

**Purpose:** Convert trading decisions into submitted orders

**Logic:**
```
Input: BrokerExecutionPlan
  1. Get appropriate broker adapter
  2. For each trade in plan:
     a. Convert to broker-specific Order format
     b. Call adapter.submit_order()
     c. Record order_id and timestamp
     d. Update order status to SUBMITTED
  3. Mark plan as IN_PROGRESS
  4. Return updated state
```

**Execution:**
- **When:** After portfolio optimization confirmed
- **Frequency:** Triggered by trading decision
- **Error Behavior:** Partial execution allowed (some orders fail, others succeed)

**Example Flow:**
```python
# Input trading decisions
state.trading_decision = TradingDecision(
    action="BUY",
    symbol="AAPL",
    qty=100,
    entry_price=150.00
)

# TradeExecutorNode processes
order = Order(
    symbol="AAPL",
    side="BUY",
    qty=100,
    type="LIMIT",
    limit_price=150.00
)

# Submits to broker
order_id = await adapter.submit_order(order)

# Records in state
state.submitted_orders.append({
    "order_id": order_id,
    "symbol": "AAPL",
    "qty": 100,
    "status": "SUBMITTED"
})
```

---

### Node 3: OrderMonitorNode

**Purpose:** Track pending orders and update status in real-time

**Logic:**
```
Monitoring loop (runs periodically):
  1. For each submitted order:
     a. Query broker for current status
     b. If filled: record fill price and timestamp
     c. If cancelled: record cancellation
     d. If new fills since last check: update state
  2. Update order status in state
  3. Detect fully filled vs partially filled
```

**Status Transitions:**
```
PENDING → SUBMITTED → PARTIALLY_FILLED → FILLED
                   ↓            ↓
                CANCELLED    PARTIALLY_CANCELLED
```

---

### Node 4: PositionManagerNode

**Purpose:** Monitor current holdings and calculate unrealized P&L

**Logic:**
```
Monitoring loop:
  1. Query current positions from broker
  2. For each position:
     a. Calculate unrealized P&L
     b. Calculate position size as % of portfolio
     c. Calculate days held
  3. Update state.broker_positions
  4. Detect new positions, closed positions, changed quantities
```

---

### Node 5: AccountMonitorNode

**Purpose:** Track account-level metrics

**Monitors:**
- Account value (cash + positions)
- Used margin / available margin (if margin trading)
- Buying power
- Account risk metrics
- Daily/monthly P&L

---

### Node 6: RiskControlNode

**Purpose:** Enforce portfolio risk limits

**Risk Checks:**
```
Before execution:
  1. Max position size: 5% of portfolio
  2. Max correlation: 0.7 between positions
  3. Max sector concentration: 20%
  4. Max leverage: 2x networth (if allowed)
  5. Stop-loss distance: Min 2% from entry

If violated:
  - Scale down position size
  - Add hedges
  - Or reject trade entirely
```

---

### Node 7: ComplianceLoggerNode

**Purpose:** Create audit trail for regulatory compliance (SEC, broker rules)

**Records:**
- All orders (submitted, cancelled, filled)
- Order modifications
- Fills and partial fills
- Position changes
- Account changes
- Errors and exceptions
- Node execution order and timing
- Risk limit violations

**Export:** JSON logs usable for SEC/broker audits

---

## Execution Workflow

### Scenario: Submit and Execution

```
1. System Decision Phase (Nodes)
   ├── DataNode: Collect market data
   ├── Analysts: Analyze (parallel)
   └── DecisionNode: → TradingDecision (BUY 100 AAPL @ $150)

2. Broker Execution Phase (This package)
   ├── TradeExecutorNode
   │   ├── Creates Order object
   │   ├── Calls adapter.submit_order()
   │   └── → Order submitted to broker, order_id=12345
   │
   ├── OrderMonitorNode (continuous)
   │   ├── Polls "Is order filled?"
   │   ├── Notices fill at $149.95
   │   └── → Updates state order status
   │
   ├── PositionManagerNode
   │   ├── Fetches positions
   │   ├── 100 AAPL @ avg_price=$149.95
   │   └── → Unrealized P&L = +$5
   │
   ├── RiskControlNode
   │   ├── Checks if position violates limits
   │   ├── ✓ OK (only 2% of portfolio)
   │   └── → Allows position
   │
   └── ComplianceLoggerNode
       └── → Records complete trade in audit log
```

---

## Configuration

### Brokers Configuration

```python
# config.py
BROKERS = {
    "alpaca": {
        "enabled": True,
        "api_key": "...",
        "secret_key": "...",
        "base_url": "https://paper-api.alpaca.markets",  # Paper for testing
        "paper_trading": True
    },
    "interactive_brokers": {
        "enabled": False,
        "host": "127.0.0.1",
        "port": 7497,
        "client_id": 1
    }
}

# Risk limits
RISK_LIMITS = {
    "max_position_pct": 0.05,  # 5% of portfolio
    "max_leverage": 2.0,
    "max_drawdown": -0.20  # 20% max
}
```

---

## Adding a New Broker

### Step 1: Create Adapter
```python
# brokers/adapters.py

class MyBrokerAdapter(BrokerAdapter):
    """Implementation for MyBroker."""
    
    async def connect(self) -> bool:
        # Connect logic
        pass
    
    async def submit_order(self, order: Order) -> str:
        # Order submission logic
        pass
    
    # ... implement all abstract methods
```

### Step 2: Register in Factory
```python
# brokers/nodes.py in BrokerConnectorNode

def _create_adapter(self, broker_id: str, account):
    if broker_id == "mybroker":
        return MyBrokerAdapter(broker_id, account)
    # ... other brokers
```

### Step 3: Add Configuration
```python
# config.py
BROKERS = {
    "mybroker": {
        "enabled": True,
        "api_key": "...",
        # ... broker-specific config
    }
}
```

### Step 4: Test
```bash
# Test connection
pytest tests/test_brokers.py::TestMyBrokerAdapter -v

# Test in graph
pytest tests/test_integration.py::TestBrokerExecution -v
```

---

## Error Handling

### Connection Errors
```python
# If connection fails, BrokerConnectorNode logs but continues
# System can use alternate broker or skip trading
try:
    await adapter.connect()
except ConnectionError as e:
    state.add_error("broker_connector", f"Connection failed: {e}")
    # Continue with other brokers
```

### Order Submission Errors
```python
# If order submission fails, record error but continue
try:
    await adapter.submit_order(order)
except ValueError as e:  # Invalid order
    state.add_error("trade_executor", f"Invalid order: {e}")
    # Skip this order, try next one
```

### Monitoring Errors
```python
# If monitoring fails, log but don't block
try:
    status = await adapter.get_order_status(order_id)
except TimeoutError:
    state.add_error("order_monitor", "Status check timeout")
    # Will retry next monitoring cycle
```

---

## Testing

### Unit Tests
```bash
# Test Alpaca adapter
pytest tests/test_brokers.py::TestAlpacaAdapter -v

# Test IB adapter
pytest tests/test_brokers.py::TestInteractiveBrokersAdapter -v
```

### Integration Tests
```bash
# Test end-to-end order flow
pytest tests/test_integration.py::TestOrderExecution -v

# Test with mock broker
pytest tests/test_brokers.py::TestBrokerNodes -v
```

### Paper Trading
```python
# Use paper trading mode before going live
BROKERS["alpaca"]["paper_trading"] = True

# Run full system in paper mode
python -m src.main --paper-trading
```

---

## Best Practices

1. **Always Test in Paper Mode First**
   ```python
   # Paper trading - no real money at risk
   alpaca_config.paper_trading = True
   ```

2. **Implement Risk Controls**
   ```python
   # Check limits before execution
   if order_value > portfolio_size * 0.05:  # Max 5%
       raise ValueError("Order too large")
   ```

3. **Use Order Types Appropriately**
   ```python
   # Use stop-loss to limit downside
   Order(side="BUY", type="LIMIT", price=150.00, stop_loss=145.00)
   ```

4. **Log Everything**
   ```python
   # Audit trail for compliance
   ComplianceLoggerNode logs all trades
   ```

5. **Handle Partial Fills**
   ```python
   # Orders might not fill completely
   if order.filled_qty < order.qty:
       # Handle partial fill
       pass
   ```

6. **Check Broker Hours**
   ```python
   # Alpaca: 9:30 AM - 4:00 PM ET only
   # IB: Extended hours available
   if not is_market_hours():
       use_extended_hours_or_delay()
   ```

---

## Limitations & Considerations

- **Alpaca:** Stock-only, no options/futures
- **Interactive Brokers:** Requires TWS/Gateway running locally
- **Paper vs Real:** Testing costs nothing; real money needs real capital
- **Latency:** Network latency affects fill prices
- **Market Hours:** Different brokers have different trading hours
- **Commissions:** Real money charges commissions; paper trading doesn't

---

## Future Enhancements

- [ ] Support for TD Direct trading
- [ ] Robinhood integration
- [ ] Crypto exchange integration
- [ ] Options approval automation
- [ ] Margin optimization
- [ ] Multi-account portfolio view
- [ ] Smart order routing

---

## Summary

| Component | Purpose | Status |
|-----------|---------|--------|
| BrokerAdapter | Abstract interface | ✅ Implemented |
| AlpacaAdapter | Stock trading | ✅ Implemented |
| InteractiveBrokersAdapter | Multi-asset trading | ✅ Implemented |
| BrokerConnectorNode | Connection setup | ✅ Implemented |
| TradeExecutorNode | Order submission | ✅ Implemented |
| OrderMonitorNode | Status tracking | ✅ Implemented |
| PositionManagerNode | Holdings tracking | ✅ Implemented |
| RiskControlNode | Limit enforcement | ✅ Implemented |
| ComplianceLoggerNode | Audit trail | ✅ Implemented |

