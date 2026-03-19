# Trading Dashboard - Quick Reference Guide

## 🚀 Quick Start (2 Minutes)

### Start the Dashboard
```bash
cd c:\projects\ai\AiMarketTrade
python web_dashboard_trading.py
```

### Access Dashboard
```
http://localhost:5000
```

### Try It Out
1. Click **"Execute Trade"** tab
2. Enter: AAPL, Buy, 10 shares, $150
3. Click **"Execute Trade"** button
4. View updated portfolio in **"Trade History"** tab

---

## 📊 Dashboard Sections

### Section 1: Portfolio Overview (Top)
```
┌─────────────────────┬─────────────────────┬─────────────────────┬─────────────────┐
│ Portfolio Value     │ Cash Balance        │ Total P&L           │ Total Return    │
│ $99,953.88          │ $58,028.88          │ -$46.12             │ -0.05%          │
└─────────────────────┴─────────────────────┴─────────────────────┴─────────────────┘
```

### Section 2: Tab Navigation
```
[Positions] [Trade History] [Execute Trade] [Performance] [Reports] [System Status]
```

### Section 3: Tab Content Areas
Each tab shows:
- **Positions**: Table of holdings
- **Trade History**: Complete trade log with fees
- **Execute Trade**: Forms for manual trades and automated cycles
- **Performance**: Detailed metrics cards
- **Reports**: Historical analysis
- **System Status**: Market monitoring

---

## 🎯 Tab-by-Tab Guide

### TAB 1: POSITIONS
```
┌────────┬──────────┬─────────┬──────────────┬──────────────┐
│ Symbol │ Quantity │ Avg Cost│ Current Value│ P&L          │
├────────┼──────────┼─────────┼──────────────┼──────────────┤
│ AAPL   │ 172      │ $151.00 │ $25,972.00   │ (+/-) YYY.YY │
│ MSFT   │ 53       │ $301.00 │ $15,953.00   │ (+/-) YYY.YY │
└────────┴──────────┴─────────┴──────────────┴──────────────┘
```

### TAB 2: TRADE HISTORY
```
┌──────────────┬────┬────────┬──────────┬──────┬──────────┬──────────┬──────────┐
│ Date/Time    │ Act│ Symbol │ Quantity │Price │ Total    │ Commission│ Slippage │
├──────────────┼────┼────────┼──────────┼──────┼──────────┼──────────┼──────────┤
│ 13:38:05 BUY │ AAP│ 66     │ $151.00  │ $9966│ $0.99    │ $9.97    │          │
│ 13:38:05 BUY │ AAP│ 59     │ $151.00  │ $8909│ $0.89    │ $8.91    │          │
└──────────────┴────┴────────┴──────────┴──────┴──────────┴──────────┴──────────┘
```

### TAB 3: EXECUTE TRADE

#### Option A: Manual Trade Execution
```
┌─────────────────────────────────────┐
│ Ticker Symbol: [AAPL             ]  │
│                                     │
│ Action: [Buy ▼]                     │
│                                     │
│ Quantity: [10                    ]  │
│                                     │
│ Price per Share: [150.00         ]  │
│                                     │
│ [       Execute Trade        ]      │
└─────────────────────────────────────┘
```

#### Option B: Automated Trading Cycle
```
┌─────────────────────────────────────┐
│ Ticker: [AAPL                    ]  │
│                                     │
│ Action: [BUY Signal ▼]              │
│                                     │
│ Signal Confidence: [0.85         ]  │
│                                     │
│ [ Run Trading Cycle - Full Auto ]   │
└─────────────────────────────────────┘
```

### TAB 4: PERFORMANCE
```
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Realized P&L     │ Unrealized P&L   │ Win Rate         │ Total Trades     │
│ $0.00            │ -$46.12          │ 0.00%            │ 5                │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Avg Profit/Win   │ Avg Loss/Loss    │ Volatility       │ Sharpe Ratio     │
│ $0.00            │ $0.00            │ 0.55             │ -0.08            │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Max Drawdown     │ Portfolio Value  │ Cash Balance     │ Open Positions   │
│ -41.93%          │ $99,953.88       │ $58,028.88       │ 2                │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

---

## 💻 API Endpoints Reference

### 1. Get Portfolio (GET)
```bash
curl http://localhost:5000/api/portfolio
```
Returns: Portfolio value, cash, P&L, positions list

### 2. Get Trades (GET)
```bash
curl http://localhost:5000/api/trades?limit=50
```
Returns: List of executed trades with fees

### 3. Get Performance (GET)
```bash
curl http://localhost:5000/api/performance
```
Returns: Metrics (P&L, win rate, volatility, etc.)

### 4. Execute Trade (POST)
```bash
curl -X POST http://localhost:5000/api/execute-trade \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "action": "buy",
    "quantity": 10,
    "price": 150.00
  }'
```
Returns: Trade confirmation with ID

### 5. Run Trading Cycle (POST)
```bash
curl -X POST http://localhost:5000/api/run-trading-cycle \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "action": "BUY",
    "confidence": 0.85
  }'
```
Returns: Cycle results (trades executed, metrics)

---

## 🎮 Common Workflows

### Workflow 1: Execute Single Trade
```
1. Open Dashboard: http://localhost:5000
2. Click "Execute Trade" tab
3. Enter:
   - Ticker: AAPL
   - Action: Buy
   - Quantity: 10
   - Price: $150
4. Click "Execute Trade"
5. Confirm in "Trade History"
```

### Workflow 2: Run Automated Trading Cycle
```
1. Open "Execute Trade" tab
2. Scroll to "Run Trading Cycle"
3. Set:
   - Ticker: AAPL
   - Action: BUY Signal
   - Confidence: 0.85 (85%)
4. Click "Run Trading Cycle"
5. Watch: Trade generation → Execution → Metrics
6. View results in "Trade History" and "Performance"
```

### Workflow 3: Monitor Portfolio
```
1. Open Dashboard homepage
2. View stats grid: Value, Cash, P&L, Return %
3. Click "Positions" tab to see holdings
4. Click "Trade History" to see all trades
5. Click "Performance" for detailed metrics
6. Use "🔄 Refresh Data" to update
```

---

## 🔧 Configuration

### Default Settings
```
Position Size:         10% of portfolio
Confidence Threshold:  70% (below this, trades are skipped)
Commission:            0.01% of trade value
Slippage:              0.1% of trade value
Initial Capital:       $100,000.00
```

### Customize Via CLI
```bash
python web_dashboard_trading.py --trading-position-size 0.05
python web_dashboard_trading.py --trading-initial-capital 50000
```

---

## 🧪 Test & Demo

### Run Demo
```bash
python demo_trading_dashboard.py
```
Shows:
- Multiple trading cycles executing
- Portfolio state tracking
- Fee/slippage calculation
- Metrics computation

### Run Tests
```bash
python -m pytest tests/test_trading_nodes.py -v
```
Result: **16/16 tests passing** ✅

---

## 📈 Understanding Metrics

| Metric | Formula | Interpretation |
|--------|---------|-----------------|
| **Total P&L** | Realized + Unrealized | Total profit/loss |
| **Win Rate** | Wins / Total Trades | % of profitable trades |
| **Return %** | P&L / Initial Capital × 100 | Overall return percentage |
| **Volatility** | Std Dev of Returns | Price fluctuation measurement |
| **Sharpe Ratio** | Return / Volatility | Risk-adjusted return |
| **Max Drawdown** | Peak-to-Trough Decline | Worst loss from high point |

---

## 🎨 UI Color Codes

| Color | Meaning |
|-------|---------|
| 🟢 Green (positive) | Profit, positive P&L |
| 🔴 Red (negative) | Loss, negative P&L |
| 🔵 Blue (badges) | BUY action badges |
| 🟠 Orange (badges) | SELL action badges |
| ⚪ Gray | Neutral/inactive status |

---

## ⚡ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Tab Key | Navigate between form fields |
| Enter | Submit form |
| Ctrl+R | Hard refresh dashboard |
| Click Tab | Switch between sections |

---

## 🆘 Troubleshooting

### Dashboard Won't Start
```bash
# Check port 5000 is available
netstat -ano | findstr :5000

# Kill process using port 5000 if needed
taskkill /PID <PID> /F
```

### Trades Not Showing
```bash
1. Check "Trade History" tab loads
2. Try clicking "🔄 Refresh Data"
3. Check browser console for errors (F12)
```

### API Errors
```bash
# Check Flask server is running
python web_dashboard_trading.py

# Test API directly
curl http://localhost:5000/api/portfolio
```

---

## 📱 Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (responsive)

---

## 📚 Full Documentation

See complete docs: `TRADING_DASHBOARD_README.md`

---

**Last Updated**: March 18, 2026
**Status**: ✅ Production Ready
