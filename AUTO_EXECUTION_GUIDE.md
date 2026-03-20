# Automatic Trade Execution Feature Guide

## Overview
The trading system now supports both **automatic** and **manual** trade execution modes. Confirmed recommendations from the scanner can be automatically executed based on confidence thresholds.

## Configuration

### Environment Variables
Set these to control auto-execution behavior:

```bash
# Enable automatic trade execution (default: false)
AUTO_EXECUTE_TRADES=true

# Minimum confidence score to execute (0-1, default: 0.70 = 70%)
AUTO_EXECUTE_MIN_CONFIDENCE=0.70

# Position size for automatic trades in dollars (default: 1000)
AUTO_EXECUTE_POSITION_SIZE=1000.0
```

### Programmatic Configuration
Or configure in code via `src/config.py`:

```python
from src.config import Settings

config = Settings()
print(config.auto_execute_trades)  # Check if enabled
print(config.auto_execute_min_confidence)  # Get confidence threshold
print(config.auto_execute_position_size)  # Get position size
```

## How It Works

### 1. **Scan Analysis** (Three Stages)
```
Stage 1: Quick Scan Filter
  └─ Technical screening of all stocks
     └─ Returns candidates with high probability signals

Stage 2: Deep Analysis  
  └─ Full validation on filter results
     └─ Confirms signals match across indicators
     └─ Assigns confidence score (0-10)

Stage 3: Automatic Execution (if enabled)
  └─ Checks each confirmed result
  └─ Verifies confidence >= threshold
  └─ Executes BUY or SELL trades
  └─ Logs execution details with reasons
```

### 2. **Execution Logic**

For each **BUY** signal:
- Convert deep score (0-10) to confidence (0-1)
- Check if confidence ≥ minimum threshold
- Verify sufficient cash available
- Calculate position size based on current price
- Execute buy order with commission/slippage

For each **SELL** signal:
- Check if position exists and has shares
- Calculate sale proceeds
- Deduct commission/slippage
- Execute sell order and close position

### 3. **Execution Details Response**

The scan result includes execution information:

```json
{
  "execution": {
    "auto_execute_enabled": true,
    "trades_executed": 2,
    "execution_details": [
      {
        "ticker": "META",
        "recommendation": "BUY",
        "deep_score": 3.8,
        "confidence": "38%",
        "executed": true,
        "reason": "Deep analysis score: 3.8/10 (38% confidence)"
      },
      {
        "ticker": "MSFT", 
        "recommendation": "SELL",
        "deep_score": 4.1,
        "confidence": "41%",
        "executed": false,
        "reason": "Confidence 41% below minimum 70%"
      }
    ],
    "executed_trades": [
      {
        "timestamp": "2026-03-20T22:56:52.123456",
        "ticker": "META",
        "action": "BUY",
        "quantity": 5,
        "price": 200.50,
        "total_value": 1002.50,
        "commission": 0.10,
        "slippage": 1.50,
        "rationale": "Auto-executed BUY from AI scan. Deep analysis score: 3.8/10..."
      }
    ]
  }
}
```

## Dashboard Display

After running a scan, you'll see:

1. **Summary Status Card** - Shows:
   - Execution mode (Enabled/Disabled)
   - Number of trades executed

2. **Execution Details Table** - Shows for each recommendation:
   - Ticker and signal direction (BUY/SELL)
   - Deep analysis score
   - Calculated confidence percentage
   - Execution status (✅ Executed / ⏳ Skipped)
   - Detailed reason explaining why it executed or was skipped

### Example Execution Reasons

**Executed:**
```
✅ Executed: Deep analysis score: 3.8/10 (38% confidence)
✅ Executed: Deep analysis score: 7.5/10 (75% confidence)
```

**Skipped:**
```
⏳ Skipped: Confidence 38% below minimum 70%
⏳ Skipped: Insufficient cash: need $1500.00, have $800.00
⏳ Skipped: No position to sell
⏳ Skipped: Error executing trade: insufficient margin
```

## API Endpoint

### POST `/api/scanner/scan-now/<industry>`

Executes a two-stage scan with optional auto-execution.

**Response:**
```json
{
  "success": true,
  "industry": "AI",
  "stages": {
    "quick": {
      "time_secs": 6.5,
      "candidates": 3,
      "results": [...]
    },
    "deep": {
      "time_secs": 0.5,
      "confirmed": 2,
      "results": [...]
    }
  },
  "execution": {
    "auto_execute_enabled": true,
    "trades_executed": 1,
    "execution_details": [...],
    "executed_trades": [...]
  },
  "message": "✅ Scan complete: 3 candidates → 2 confirmed → 1 auto-executed"
}
```

## Best Practices

1. **Start Conservative**
   - Enable auto-execution with minimum confidence at 80-90%
   - Use smaller position sizes initially
   - Monitor results for 1-2 weeks

2. **Monitor Execution**
   - Check dashboard execution details after each scan
   - Review the reasons trades were skipped
   - Adjust thresholds based on performance

3. **Risk Management**
   - Set reasonable position sizes (don't over-leverage)
   - Monitor cash balance to prevent execution failures
   - Use stop-losses for additional protection

4. **Hybrid Approach** (Recommended)
   - Keep auto-execution disabled by default
   - Use manual mode to review recommendations
   - Enable auto-execution only for high-confidence signals
   - Maintain manual override capability

## Troubleshooting

### Trades Not Executing
**Problem:** Confidence shows 38% but minimum is 70%, so trades are skipped.
**Solution:** Either (a) lower the minimum threshold, or (b) improve signal strength in deep analysis.

### Insufficient Cash Error
**Problem:** Execution details show "Insufficient cash" reason.
**Solution:** (a) Reduce position size, (b) close existing positions, (c) add more capital.

### No Position to Sell  
**Problem:** SELL signal but no position exists.
**Solution:** This is expected if position was already closed or never existed. Safe to skip.

## Monitoring

Track execution through:
1. **Dashboard** - Visual execution details after each scan
2. **Logs** - Full execution details in console/log file
3. **Trade History** - View all executed trades in `/api/trades` endpoint
4. **Portfolio** - Check positions and cash balance in `/api/portfolio` endpoint

## Disabling Auto-Execution

To switch back to manual-only mode:

```bash
# Via environment variable
AUTO_EXECUTE_TRADES=false

# Or manually set in config
config.auto_execute_trades = False
```

All confirmed recommendations will still be displayed in the dashboard for manual review and execution.
