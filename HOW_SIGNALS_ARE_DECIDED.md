# How the Scanner Decides BUY/SELL/HOLD Signals

## Quick Summary
The scanner uses a **scoring system** with 3 technical indicators:
1. **RSI** (Relative Strength Index) - Momentum
2. **Volume Spike** - Unusual trading activity
3. **MACD** (Moving Average Convergence Divergence) - Trend

Each indicator contributes points. Whichever score is higher wins!

---

## The Scoring System

### 📊 Signal 1: RSI (Relative Strength Index)

**What it measures:** Stock momentum (is it moving up or down too fast?)

**The Scale:**
```
RSI Value      |  Meaning           | Points Added
───────────────┼────────────────────┼──────────────
0-30           | OVERSOLD           | +2 to BUY
30-70          | NEUTRAL (Normal)   | +0 (no signal)
70-100         | OVERBOUGHT         | +2 to SELL
```

**Example 1: AAPL with RSI=22 (OVERSOLD)**
```
RSI Value: 22
Condition: < 30 = OVERSOLD
Interpretation: Stock fell too much too fast
Action: Add +2 to BUY score ✓
Signal: "This might bounce back - consider BUYING"
```

**Example 2: PLTR with RSI=76 (OVERBOUGHT)**
```
RSI Value: 76
Condition: > 70 = OVERBOUGHT
Interpretation: Stock went up too much too fast
Action: Add +2 to SELL score ✓
Signal: "This might pull back - consider SELLING"
```

**Example 3: NVDA with RSI=47 (NEUTRAL)**
```
RSI Value: 47
Condition: 30-70 = NEUTRAL
Interpretation: Stock moving normally, no extreme
Action: Add +0 to either score
Signal: "No momentum signal yet"
```

---

### 📈 Signal 2: Volume Spike Detection

**What it measures:** Is trading volume unusual? (High volume = strong conviction)

**The Logic:**
```
Recent Volume vs Average Volume
───────────────────────────────
Recent Vol / Avg Vol > 1.5x  →  SPIKE DETECTED! (+1 to BUY)
Recent Vol / Avg Vol ≤ 1.5x  →  Normal volume (no signal)
```

**Example 1: Stock with Volume Spike**
```
Recent Volume (today):   1,000,000 shares
Average Volume (20-day): 600,000 shares
Ratio: 1,000,000 / 600,000 = 1.67x
Decision: 1.67 > 1.5? YES! 
Result: Volume spike detected! +1 to BUY score ✓

Interpretation: High volume confirms buying interest
```

**Example 2: Stock with Normal Volume**
```
Recent Volume (today):   600,000 shares
Average Volume (20-day): 500,000 shares
Ratio: 600,000 / 500,000 = 1.2x
Decision: 1.2 > 1.5? NO
Result: Normal volume (no bonus points)

Interpretation: Nothing unusual, keep watching
```

---

### 🔄 Signal 3: MACD (Moving Average Convergence Divergence)

**What it measures:** Trend changes (when momentum is shifting)

**The Mechanics:**
```
MACD Line:     Fast moving average (12-day EMA)
Signal Line:   Slow moving average (26-day EMA)  
Histogram:     The difference (MACD - Signal)

When MACD crosses above Signal → BUY SIGNAL (+2 to BUY score)
When MACD crosses below Signal → SELL SIGNAL (+2 to SELL score)
```

**Visual Example:**

```
MACD > Signal (Bullish)        MACD < Signal (Bearish)
─────────────────────          ───────────────────────
       MACD Line /                    MACD Line \
            /   Signal Line ---           \ Signal Line ---
           /        /                      \        /
          / BUY ↗  /                       \ SELL ↘\
         /       /                          \       \
```

**Real Example: Stock with MACD Buy Cross**
```
Time t-1 (yesterday):  MACD = 0.8,  Signal = 0.9  (MACD below)
Time t   (today):      MACD = 1.2,  Signal = 0.9  (MACD above!)

What happened: MACD crossed ABOVE the signal line
Action: ADD +2 to BUY score ✓
Signal: "Momentum is turning bullish"
```

**Real Example: Stock with MACD Sell Cross**
```
Time t-1 (yesterday):  MACD = 1.5,  Signal = 1.4  (MACD above)
Time t   (today):      MACD = 1.1,  Signal = 1.4  (MACD below!)

What happened: MACD crossed BELOW the signal line
Action: ADD +2 to SELL score ✓
Signal: "Momentum is turning bearish"
```

---

## How Points Add Up - Real Examples

### Complete Example 1: STRONG BUY Signal

**Stock: ABC with the following conditions:**
```
RSI:              22 (OVERSOLD)      +2 BUY points ✓
Volume:           2.0x average       +1 BUY points ✓
MACD:             Just crossed above +2 BUY points ✓
─────────────────────────────────────────────────
Total BUY score:  5 points
Total SELL score: 0 points

Decision: 5 > 0  →  BUY ✓✓✓ (Strong signal!)
Confidence: HIGH - Multiple indicators agree
```

**Interpretation:**
- Stock fell too much (RSI oversold)
- Lots of new buying activity (volume spike)
- Trend is turning positive (MACD cross)
- **All 3 say: BUY!** → Confident BUY signal

---

### Complete Example 2: STRONG SELL Signal

**Stock: XYZ with the following conditions:**
```
RSI:              75 (OVERBOUGHT)    +2 SELL points ✓
Volume:           0.9x average       +0 (no spike)
MACD:             Just crossed below +2 SELL points ✓
─────────────────────────────────────────────────
Total BUY score:  0 points
Total SELL score: 4 points

Decision: 4 > 0  →  SELL ✓✓ (Strong signal!)
Confidence: HIGH - RSI + MACD agree
```

**Interpretation:**
- Stock went up too much (RSI overbought)
- Trend is turning negative (MACD cross)
- No volume spike to confirm buying
- **Signals say: SELL!** → Confident SELL signal

---

### Complete Example 3: HOLD (Conflicting Signals)

**Stock: DEF with the following conditions:**
```
RSI:              55 (NEUTRAL)       +0 points
Volume:           1.3x average       +0 (below 1.5x threshold)
MACD:             No crossover yet   +0 points
─────────────────────────────────────────────────
Total BUY score:  0 points
Total SELL score: 0 points

Decision: 0 = 0  →  HOLD ✓ (Wait for clarity)
Confidence: LOW - No strong signal
```

**Interpretation:**
- Stock trading normally (RSI neutral)
- Nothing unusual in volume
- Trend hasn't shifted yet (no MACD cross)
- **Decision: HOLD** - Not enough evidence yet

---

### Edge Case: Mixed Signals

**Stock: MIX showing conflicting signals:**
```
RSI:              25 (OVERSOLD)      +2 BUY points
Volume:           0.8x average       +0 (no spike)
MACD:             Crossed below      +2 SELL points
─────────────────────────────────────────────────
Total BUY score:  2 points
Total SELL score: 2 points

Decision: 2 = 2  →  HOLD (Signals contradict)
Confidence: MEDIUM - Need more data
```

**Interpretation:**
- RSI says: "Stock oversold, buy it"
- MACD says: "Trend turning negative, sell it"
- Volume says: "Not interesting right now"
- **Decision: HOLD** - Wait for clarification

---

## Real-World Example from Scanner Output

From our test run, here's what actually happened:

### Stock: NVDA (NVIDIA)
```
Current Price: $182.76
Volume Ratio: 1.2x (no spike, need >1.5x)
RSI: 47.47 (NEUTRAL - between 30-70)
MACD: No recent crossover

Scoring:
├─ RSI Contribution:      0 points (neutral)
├─ Volume Contribution:   0 points (normal)
├─ MACD Contribution:     0 points (no cross)
└─ Total: BUY=0, SELL=0

Result: HOLD ⚪
Why: Stock trading normally, no strong signal
```

### Stock: PLTR (Palantir)
```
Current Price: $155.52
Volume Ratio: 1.1x (normal)
RSI: 75.94 (OVERBOUGHT - above 70)
MACD: Previous histogram suggests sell signal

Scoring:
├─ RSI Contribution:      +2 to SELL (overbought!)
├─ Volume Contribution:   0 points (normal)
├─ MACD Contribution:     +2 to SELL (bearish cross)
└─ Total: BUY=0, SELL=4

Result: SELL 🔴
Why: Stock overextended and trend reversing
```

### Stock: AAPL (Apple)
```
Current Price: $253.13
Volume Ratio: 0.9x (low volume)
RSI: 22.36 (OVERSOLD - below 30)
MACD: No crossover detected yet

Scoring:
├─ RSI Contribution:      +2 to BUY (oversold!)
├─ Volume Contribution:   0 points (low volume = weak signal)
├─ MACD Contribution:     0 points (no cross)
└─ Total: BUY=2, SELL=0

Result: WAIT ⚪ or Weak BUY
Why: RSI says buy, but volume doesn't confirm (needs both)
Confidence: LOW without volume confirmation
```

---

## Decision Matrix - Quick Reference

| Scenario | RSI | Volume | MACD | Total Buy | Total Sell | Decision |
|----------|-----|--------|------|-----------|------------|----------|
| Very Strong | +2 BUY | +1 BUY | +2 BUY | 5 | 0 | 🟢 BUY |
| Strong Buy | +2 BUY | - | +2 BUY | 4 | 0 | 🟢 BUY |
| Weak Buy | +2 BUY | - | - | 2 | 0 | ⚪ HOLD |
| Neutral | - | - | - | 0 | 0 | ⚪ HOLD |
| Weak Sell | +2 SELL | - | - | 0 | 2 | ⚪ HOLD |
| Strong Sell | +2 SELL | - | +2 SELL | 0 | 4 | 🔴 SELL |
| Conflict | +2 BUY | - | +2 SELL | 2 | 2 | ⚪ HOLD |

---

## Why This System Works

### ✅ Advantages

1. **Multiple Confirmations**
   - One indicator can be wrong
   - If 2-3 agree, higher confidence

2. **Risk Management**
   - Won't buy on weak signals
   - Requires genuine conviction

3. **Avoids False Alarms**
   - Random volume spike alone won't trigger
   - Random RSI blip alone won't trigger
   - Need convergence

4. **Adapts to Market Conditions**
   - Oversold stocks less risky to buy
   - Overbought stocks more likely to reverse
   - Volume confirms buying/selling interest

### ⚠️ Limitations

1. **Lagging Indicators**
   - RSI/MACD based on historical prices
   - May miss sudden news/events

2. **Need Time for Signals**
   - MACD crossovers take time
   - Volume spikes are point-in-time events

3. **Works Best in Trending Markets**
   - During sideways trading: many false signals
   - Strong trends: signals align well

---

## How to Adjust Sensitivity

### To Get MORE Signals (Aggressive):
```python
# Lower RSI thresholds
RSI_OVERSOLD_THRESHOLD = 40   # was 30 (easier to trigger BUY)
RSI_OVERBOUGHT_THRESHOLD = 60 # was 70 (easier to trigger SELL)

# Lower volume spike threshold  
VOLUME_SPIKE_RATIO = 1.2      # was 1.5 (easier to trigger)

# Or remove requirement for multiple confirmations
if any([rsi_buy, volume_spike, macd_buy]):  # ANY trigger
    BUY
```

### To Get FEWER Signals (Conservative):
```python
# Stricter RSI thresholds
RSI_OVERSOLD_THRESHOLD = 20    # was 30 (harder to trigger)
RSI_OVERBOUGHT_THRESHOLD = 80  # was 70 (harder to trigger)

# Require more confirmations
if (rsi_buy and macd_buy):     # BOTH must trigger
    BUY
```

### Current Settings (Balanced):
```python
RSI_OVERSOLD = 30    # Standard definition
RSI_OVERBOUGHT = 70  # Standard definition
VOLUME_SPIKE = 1.5x  # 50% above average = significant
MIN_SCORE = 2        # Need at least 2 points to rank high
```

---

## Summary

The scanner decides using this logic:

```
FOR EACH STOCK:
  1. Calculate RSI (momentum check)
     ├─ If RSI < 30  → +2 BUY points
     └─ If RSI > 70  → +2 SELL points
  
  2. Calculate Volume Spike (conviction check)
     └─ If volume > 1.5x average → +1 BUY point
  
  3. Calculate MACD (trend check)
     ├─ If MACD crosses above → +2 BUY points
     └─ If MACD crosses below → +2 SELL points
  
  4. Compare Scores
     ├─ If buy_score > sell_score   → BUY 🟢
     ├─ If sell_score > buy_score   → SELL 🔴
     └─ If scores equal or both 0   → HOLD ⚪
  
  5. Recommend → Only show if score ≥ 2
```

**Result: Intelligent, multi-factor trading signals based on real market data!** ✓

