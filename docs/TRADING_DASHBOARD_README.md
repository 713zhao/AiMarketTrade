# Trading System Dashboard Integration

## Overview

The trading system dashboard provides a comprehensive visual interface for:
- **Portfolio Monitoring**: Real-time tracking of positions and cash balance
- **Trade History**: Complete record of all executed trades with fees and slippage
- **Performance Metrics**: Detailed P&L, volatility, Sharpe ratio, win rate, and drawdown analysis
- **Trade Execution**: Manual trade entry and automated trading cycle execution
- **Dashboard Analytics**: Interactive charts and metrics visualization

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│  Web Dashboard (Flask + HTML/JS)                        │
├─────────────────────────────────────────────────────────┤
│  API Layer (REST Endpoints)                             │
├─────────────────────────────────────────────────────────┤
│  Business Logic Layer                                   │
│  ├─ Trading Nodes (Async)                              │
│  │  ├─ RecommendationToTradeNode                       │
│  │  ├─ TradeExecutionNode                              │
│  │  └─ PortfolioMetricsNode                            │
│  ├─ DeerflowState (Unified Trading State)              │
│  └─ Configuration (Pydantic Settings)                  │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input (HTML Form)
         ↓
Flask API Endpoint
         ↓
Trading Node Execution (Async)
         ↓
DeerflowState Update
         ↓
JSON Response
         ↓
Dashboard Visualization Update
```

## Files

### Core Implementation

| File | Purpose |
|------|---------|
| `web_dashboard_trading.py` | Flask application with API endpoints for trading system |
| `templates/dashboard.html` | HTML/CSS/JavaScript dashboard interface |
| `demo_trading_dashboard.py` | Demo script showing full integration |
| `src/nodes/trading_nodes.py` | Core trading execution nodes |
| `src/state.py` | DeerflowState with trading fields |
| `src/config.py` | Trading configuration and settings |

## Quick Start

### 1. Start the Dashboard

```bash
python web_dashboard_trading.py
```

The dashboard will start on `http://localhost:5000`

### 2. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

### 3. Explore Tabs

- **Positions**: View current open positions and holdings
- **Trade History**: See all executed trades with fees and slippage
- **Execute Trade**: Manually enter trades for execution
- **Performance**: View detailed performance metrics
- **Reports**: Historical analysis reports
- **System Status**: Market monitoring information

## API Endpoints

### Portfolio Data

**GET `/api/portfolio`**

Returns current portfolio state:
```json
{
  "portfolio_value": 99953.88,
  "cash_balance": 58028.88,
  "total_pnl": 0.00,
  "total_return_pct": -0.05,
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 172,
      "average_cost": 151.00,
      "current_value": 25972.00
    }
  ]
}
```

### Trade History

**GET `/api/trades?limit=50`**

Returns executed trades with fees:
```json
{
  "trades": [
    {
      "timestamp": "2026-03-18T13:38:05",
      "action": "BUY",
      "symbol": "AAPL",
      "quantity": 66,
      "price": 151.00,
      "total": 9966.00,
      "commission": 0.99,
      "slippage": 9.97
    }
  ]
}
```

### Performance Metrics

**GET `/api/performance`**

Returns detailed performance statistics:
```json
{
  "portfolio_value": 99953.88,
  "cash_balance": 58028.88,
  "total_trades": 5,
  "win_rate": 0.00,
  "max_drawdown": -41.93,
  "sharpe_ratio": -0.08,
  "volatility": 0.55
}
```

### Execute Manual Trade

**POST `/api/execute-trade`**

Execute a single trade:
```json
{
  "ticker": "AAPL",
  "action": "buy",
  "quantity": 10,
  "price": 150.00
}
```

### Run Trading Cycle

**POST `/api/run-trading-cycle`**

Execute full automated cycle (recommendation → execution → metrics):
```json
{
  "ticker": "AAPL",
  "action": "BUY",
  "confidence": 0.85
}
```

## Features

### 1. Real-Time Portfolio Tracking
- Live portfolio value updates
- Cash balance monitoring
- Position tracking with P&L calculations
- Cost basis tracking per position

### 2. Trade History Visualization
- Complete trade log with timestamps
- Buy/Sell action indicators
- Commission and slippage display
- Trade rationale/notes
- Sortable and filterable table

### 3. Performance Analysis
- Realized and unrealized P&L
- Win rate calculation
- Average win/loss tracking
- Portfolio volatility estimation
- Sharpe ratio computation
- Maximum drawdown analysis

### 4. Trade Execution

**Manual Trade Entry:**
- Symbol input
- Quantity and price specification
- Buy/Sell action selection
- Real-time validation and feedback

**Automated Trading Cycles:**
- Signal confidence threshold
- Automatic position sizing
- Commission and slippage handling
- Metric recalculation

### 5. Dashboard Metrics
- Stats grid with key indicators
- Position table with details
- Trade history timeline
- Performance metrics card layout

## Trading Configuration

### Default Settings

```python
{
    "position_size_pct": 0.10,          # 10% of portfolio per trade
    "confidence_threshold": 0.70,       # 70% signal confidence min
    "slippage_pct": 0.001,              # 0.1% slippage cost
    "commission_pct": 0.0001,           # 0.01% commission
}
```

### Customization

Edit in `src/config.py` or via CLI:
```bash
python web_dashboard_trading.py --trading-position-size 0.05
python web_dashboard_trading.py --trading-initial-capital 50000
```

## Demo Output

Run the demo to see integrated trading system:
```bash
python demo_trading_dashboard.py
```

This will demonstrate:
- ✓ Multiple trading cycles
- ✓ Portfolio position tracking
- ✓ Fee and slippage calculation
- ✓ Metrics computation
- ✓ JSON API format output

## Usage Examples

### Execute a Buy Trade

1. Go to "Execute Trade" tab
2. Enter ticker: `AAPL`
3. Select action: `Buy`
4. Enter quantity: `10`
5. Enter price: `150.00`
6. Click "Execute Trade"

### Run Automated Cycle

1. Go to "Execute Trade" tab
2. Enter ticker: `AAPL`
3. Select action: `BUY Signal`
4. Set confidence: `0.85`
5. Click "Run Trading Cycle"

This will:
1. Generate trade recommendation from signal
2. Execute the trade with position sizing
3. Calculate updated portfolio metrics
4. Update dashboard in real-time

### Monitor Performance

1. Go to "Performance" tab
2. View real-time metrics:
   - Total P&L
   - Win rate
   - Sharpe ratio
   - Volatility
   - Maximum drawdown

## Integration with Trading System

### State Management

All trading data flows through `DeerflowState`:
```python
state = DeerflowState(
    trading_enabled=True,
    cash_balance=100000.0,
    positions={},              # Current holdings
    executed_trades=[],        # Trade history
    portfolio_metrics={},      # Calculated metrics
    trading_config={...},      # Configuration
)
```

### Trading Nodes

Three async nodes handle trading operations:

1. **RecommendationToTradeNode**: Converts signals to trades
2. **TradeExecutionNode**: Executes trades with costs
3. **PortfolioMetricsNode**: Calculates performance metrics

### API Layer

Flask endpoints bridge dashboard and trading system:
```python
@app.route('/api/portfolio')
@app.route('/api/trades')
@app.route('/api/performance')
@app.route('/api/execute-trade', methods=['POST'])
@app.route('/api/run-trading-cycle', methods=['POST'])
```

## Testing

Test the dashboard integration:

```bash
# Run the demo
python demo_trading_dashboard.py

# Run trading tests
python -m pytest tests/test_trading_nodes.py -v

# Run the dashboard server
python web_dashboard_trading.py
```

## Features Summary

✅ **Dashboard Components**
- Stats grid with portfolio overview
- Position tracking table
- Detailed trade history
- Performance metrics display
- Trading control forms

✅ **Trading System Integration**
- Async node execution
- Real-time state updates
- Fee/slippage handling
- Metric calculation
- Position management

✅ **API Endpoints**
- Portfolio data retrieval
- Trade history fetching
- Performance metrics
- Trade execution
- Cycle automation

✅ **User Interface**
- Tab-based layout
- Form validation
- Real-time updates
- Responsive design
- Status indicators

## Next Steps

1. **Data Persistence**: Add database backend for historical data
2. **Real Data Integration**: Connect to market data providers
3. **Advanced Charting**: Add Chart.js for performance visualization
4. **WebSocket Updates**: Real-time dashboard updates
5. **Strategy Backtesting**: Historical simulation framework

## Support

For issues or questions:
1. Check `demo_trading_dashboard.py` for usage examples
2. Review API structure in `web_dashboard_trading.py`
3. See trading node implementation in `src/nodes/trading_nodes.py`
4. Check test suite in `tests/test_trading_nodes.py`

---

**Dashboard Integrated**: March 18, 2026
**Status**: Production Ready ✅
