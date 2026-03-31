# AITradeAgent: Critical Bugfixes (2026-03-31)

**Status**: ✅ All fixes applied and verified  
**Service**: Finance Service (`localhost:8801`)  
**Date**: March 31, 2026  

## Overview

During routine operation, the AITradeAgent system experienced a prolonged period with no trades generated. Investigation revealed multiple bugs across different components. This document summarizes the root causes and fixes applied.

---

## Issues and Resolutions

### 1. Market Scanner Limit Too Low

**Problem**: The scanner only processed 10 symbols per cycle (default limit). Due to alphabetical ordering, these 10 symbols were all in a downtrend, so the `sma20_trend` strategy correctly produced no buy signals. The remainder of the 25-symbol universe was never scanned.

**Fix**:
- Added `market_scan.limit: 100` to `config/finance.yaml`
- Updated `MarketScannerAgent` to use configured limit by default

**Result**: All universe symbols are now scanned each cycle, generating signals across the full dataset.

---

### 2. ExecutionAgent Import Error

**Problem**: Missing `from datetime import datetime` caused a `NameError` when constructing trade IDs. This prevented trade execution entirely.

**Fix**: Added the missing import in `finance_service/agents/execution_agent.py`.

---

### 3. Orchestrator Event Handler Bug

**Problem**: `MainOrchestratorAgent.handle_trade_executed` attempted to construct an `AgentReport` from `event.data`, but the event data from ExecutionAgent contains `{"execution_result": {...}}`, not AgentReport fields. This raised an exception and prevented portfolio updates.

**Original Code** (app.py):
```python
execution_report = AgentReport(**event.data)  # Bad
execution_result = execution_report.payload.get("execution_result", {})
```

**Fix**: Directly extract the execution result:
```python
execution_result = event.data.get("execution_result", {})
```

**Result**: PortfolioAgent now receives trade data correctly.

---

### 4. Payload Key Mismatch

**Problem**: ExecutionAgent sent execution result with key `filled_price`, but PortfolioAgent expected `price`. This caused the trade to be recorded with a missing price, breaking position averages.

**Fix**: Changed ExecutionAgent to use `price` instead of `filled_price`:
```python
execution_result = {
    "trade_id": ...,
    "symbol": ...,
    "action": ...,
    "quantity": ...,
    "price": trade_proposal.target_price,  # was 'filled_price'
    ...
}
```

---

### 5. Missing `entry_price` in Position API

**Problem**: The dashboard UI expects an `entry_price` field in position objects, but the Position model only returned `avg_cost`. This caused the dashboard to display "Entry Price: None".

**Fix**: Added `"entry_price": self.avg_cost` as an alias in `Position.to_dict()` in `finance_service/portfolio/models.py`.

**Result**: Dashboard now shows the correct entry price.

---

## Verification

After applying all fixes and restarting the service:

- ✅ Health endpoint returns 200 OK (PID 270735)
- ✅ Portfolio state returns 200 with correct data
- ✅ First trade executed: 1398.HK BUY @ $6.74
- ✅ Position opened, quantity aggregated correctly
- ✅ Trade count increased over time (5 trades observed)
- ✅ `entry_price` present in position JSON

```json
{
  "symbol": "1398.HK",
  "quantity": 5.0,
  "avg_cost": 6.739999771118164,
  "entry_price": 6.739999771118164,
  ...
}
```

---

## Files Modified

| File | Change |
|------|--------|
| `config/finance.yaml` | Added `market_scan.limit: 100` |
| `finance_service/agents/execution_agent.py` | Added datetime import; changed `filled_price` → `price` |
| `finance_service/app.py` | Fixed `handle_trade_executed` to directly use `event.data` |
| `finance_service/portfolio/models.py` | Added `entry_price` alias in `to_dict()` |
| `finance_service/agents/market_scanner_agent.py` | Use configured limit |

---

## Impact

The AITradeAgent system is now fully autonomous:
- Market scanner covers full universe
- Trades execute automatically upon signal generation
- Portfolio updates correctly reflect positions
- Dashboard displays accurate data

No trades were lost during the outage; the system resumed normal operation.

---

## Next Steps

- Persistence: Implement database to survive restarts
- Position sizing: Use dynamic sizing based on account equity and risk limits
- Advanced performance metrics: Sharpe ratio, max drawdown calculations
