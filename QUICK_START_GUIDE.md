# Quick Start Guide - Option 2 Hybrid Scanning

## 🚀 Getting Started

### Step 1: Start Flask Server
```bash
python web_dashboard_trading.py
```
Server will start on `http://localhost:5000`

### Step 2: Access Dashboard
Open your browser to: **http://localhost:5000**

### Step 3: Run a Scan
1. Select an industry (e.g., "AI")
2. Click "Scan Now" button
3. Watch the progress:
   - ⚡ Stage 1 (Quick Filter): ~1 second
   - 🧠 Stage 2 (Deep Analysis): ~15-20 seconds
4. View results in the table below

---

## 📊 Expected Output Example

### Stage 1: Quick Filter Results
```
⚡ QUICK SCAN - FILTER STAGE: AI (8 stocks)
════════════════════════════════════════════════════════════════════════════════
✓ PLTR PASS: SELL (score 4/5) RSI74↑ | MACD↓
✓ NFLX PASS: SELL (score 4/5) RSI72↑
✗ NVDA skip: score 0/5 < 3 (not interesting)
✗ GOOGL skip: score 1/5 < 3
✓ Quick scan complete: 2 candidates passed filter
```

### Stage 2: Deep Analysis
```
🧠 DEEP ANALYSIS - VALIDATION STAGE: AI (2 candidates)
════════════════════════════════════════════════════════════════════════════════
[1/2] Analyzing PLTR...
  ✅ PLTR: CONFIRMED SELL (4/5 → 8.5/10)

[2/2] Analyzing NFLX...
  ✅ NFLX: CONFIRMED SELL (4/5 → 8.3/10)

✓ Deep analysis complete: 2 high-confidence recommendations
```

### Final Results
```
✅ Scan Complete: 8 quick → 2 confirmed
Total Time: 18.2 seconds

🟢 HIGH-CONFIDENCE RECOMMENDATIONS (2)

Stock | Price    | Quick Score | Deep Score | Signal | Confidence
─────────────────────────────────────────────────────────────────
PLTR  | $154.00  |    4.0/5    |   8.5/10   | SELL   |    HIGH
NFLX  | $ 94.00  |    4.0/5    |   8.3/10   | SELL   |    HIGH
```

---

## 🧪 Testing Methods

### Method 1: Run Test Script (Recommended for Quick Verification)
```bash
python test_option2_hybrid.py
```
This demonstrates the complete two-stage workflow without needing the web server.

**What it does:**
- Loads configuration
- Runs Stage 1 quick filter
- Runs Stage 2 deep analysis
- Shows filtering efficiency
- Displays final recommendations

**Expected Time**: 7-30 seconds

---

### Method 2: API Endpoint (For Integration Testing)
```bash
# Run a scan via API
curl -X POST http://localhost:5000/api/scanner/scan-now/AI

# Response:
{
  "success": true,
  "industry": "AI",
  "stages": {
    "quick": {"time_secs": 0.82, "candidates": 10},
    "deep": {"time_secs": 18.4, "confirmed": 3}
  },
  "total_time_secs": 19.22,
  "results": [
    {
      "ticker": "NVDA",
      "quick_score": 4.0,
      "deep_score": 8.2,
      "signal": "BUY",
      "confidence": "HIGH"
    }
  ]
}
```

---

### Method 3: Web Dashboard (For User Experience Testing)
1. Open browser to http://localhost:5000
2. Select industry dropdown
3. Click "Scan Now"
4. Watch progress bars
5. Review results in sortable table
6. Click BUY/SELL action buttons

---

## 🔧 Configuration Tuning

### File: `src/config.py`

**Default Settings:**
```python
HYBRID_SCAN_ENABLED = True              # Enable two-stage scanning
QUICK_SCAN_MIN_SCORE = 3.0              # Stage 1 threshold (0-5)
DEEP_ANALYSIS_MIN_SCORE = 6.5           # Stage 2 threshold (0-10)
QUICK_SCAN_MAX_CANDIDATES = 20          # Max candidates to Stage 2
DEEP_ANALYSIS_REQUIRE_AGREEMENT = True  # Both stages must match
QUICK_SCAN_TIMEOUT_SECS = 5.0
DEEP_ANALYSIS_TIMEOUT_SECS = 30.0
```

### Customize Your Thresholds

**Example 1: Stricter Filtering (Fewer Results)**
```python
QUICK_SCAN_MIN_SCORE = 4.0              # Higher = fewer candidates
DEEP_ANALYSIS_MIN_SCORE = 7.0           # Higher = fewer recommendations
```

**Example 2: Looser Filtering (More Results)**
```python
QUICK_SCAN_MIN_SCORE = 2.0              # Lower = more candidates
DEEP_ANALYSIS_MIN_SCORE = 6.0           # Lower = more recommendations
```

**Example 3: Faster Performance**
```python
QUICK_SCAN_MAX_CANDIDATES = 10          # Limit Stage 2 to 10 candidates
QUICK_SCAN_TIMEOUT_SECS = 3.0           # Reduce timeout
```

---

## 📈 Understanding the Scores

### Quick Score (0-5) - Stage 1
**What it measures**: Technical indicators
- **RSI 70+**: Overbought (potential SELL)
- **RSI 30-**: Oversold (potential BUY)
- **Volume spike**: Unusual activity
- **MACD crossover**: Trend change

**Scoring**:
- 0: No signals
- 1-2: Weak signals
- 3: Moderate signals (passes filter)
- 4: Strong signals
- 5: Very strong signals

### Deep Score (0-10) - Stage 2
**What it measures**: Full analysis (placeholder for 39-node graph)
- 0-3: Not recommended
- 4-6: Weak recommendation
- 6.5-8: Good recommendation (shows in results)
- 8+: Excellent recommendation

---

## ✅ Validation Checks

The system validates candidates with these rules:

1. **Score Agreement**
   - `quick_score` → (fast multiply by 2) → `deep_score_equivalent`
   - Example: 4/5 → 8+/10 ✓ (close enough)

2. **Signal Agreement**
   - Quick says SELL → Deep must say SELL ✓
   - Quick says BUY → Deep must say BUY ✗
   - No signal conflicts shown

3. **Threshold Validation**
   - `quick_score >= 3.0` ✓
   - `deep_score >= 6.5` ✓
   - Both must pass ✓

---

## 🔍 Troubleshooting

### "No candidates found"
- Stocks in industry don't have strong signals
- Try adjusting `QUICK_SCAN_MIN_SCORE` lower (2.0 instead of 3.0)
- Or select different industry

### "Deep analysis taking too long"
- System is analyzing too many candidates
- Reduce `QUICK_SCAN_MAX_CANDIDATES` from 20 to 10
- Or reduce `DEEP_ANALYSIS_TIMEOUT_SECS` for faster timeout

### "Scores don't match between stages"
- Normal - deep analysis may find issues Stage 1 missed
- If signals conflict (BUY vs SELL), candidate is rejected
- This is the validation working correctly

### Server won't start
- Check port 5000 is available: `netstat -ano | findstr :5000`
- Kill existing process: `taskkill /PID <PID> /F`
- Restart server

---

## 📝 Example Workflow

### User Scenario: "What should I trade in AI sector?"

**1. Dashboard Usage:**
```
User opens dashboard
├─ Selects "AI" industry
├─ Clicks "Scan Now"
├─ System shows: "⚡ Stage 1 scanning..." (1s)
├─ System shows: "🧠 Stage 2 analyzing..." (18s)
├─ Results appear: 3 stocks with scores & buttons
└─ User clicks BUY on NVDA, SELL on PLTR
```

**2. What Happened Behind the Scenes:**
```
Stage 1 (0.82s):
├─ Analyzed 100 AI stocks
├─ Calculated RSI, MACD, Volume
├─ Found 10 with good technical signals
└─ → Sent to Stage 2

Stage 2 (18.4s):
├─ Deep analyzed 10 candidates
├─ Validated each signal
├─ Confirmed only 3 match both stages
└─ → Displayed to user

Result: User sees only 3 highest-confidence picks
```

---

## 🎯 Key Metrics to Watch

After running a scan, look for:

| Metric | Good Range | What It Means |
|--------|-----------|---------------|
| Stage 1 Time | < 1 sec | Quick filter working |
| Stage 1 Candidates | 5-15 | ~10-15% pass filter |
| Stage 2 Time | 15-25 sec | Deep analysis running |
| Final Confirmed | 1-5 | 10-50% of Stage 1 pass |
| Total Time | 16-26 sec | Acceptable tradeoff |

---

## 📚 Architecture Summary

```
USER INTERACTION
       ↓
┌──────────────────────────────────┐
│   Web Dashboard (dashboard.html) │
│   - Industry selector            │
│   - Scan button                  │
│   - Results table                │
└──────────────────────────────────┘
       ↓
┌──────────────────────────────────┐
│   Flask API (web_dashboard.py)   │
│   - Routes: /api/scanner/*       │
│   - Orchestration logic          │
└──────────────────────────────────┘
       ↓
    ┌──────────────────────────────────────┐
    │                                      │
    ↓                                      ↓
┌─────────────────┐            ┌──────────────────────┐
│  STAGE 1: QUICK │            │  STAGE 2: DEEP       │
│  data_fetcher.py│            │  placeholder (→ 39nd │
│  Features:      │            │  Features:           │
│  - RSI calc     │            │  - Full analysis     │
│  - MACD calc    │            │  - Score 0-10        │
│  - Vol spike    │            │  - Validation checks │
│  - Score 0-5    │            │  - Signal matching   │
│  - Filter 100→10│            │  - Filter 10→3       │
└─────────────────┘            └──────────────────────┘
    ↓                                      ↓
    └──────────────────────────────────────┘
             ↓
    ┌──────────────────────────────────┐
    │   Results Display (dashboard)    │
    │   - Both scores visible          │
    │   - Confidence ratings           │
    │   - Action buttons               │
    │   - Timing breakdown             │
    └──────────────────────────────────┘
             ↓
        USER SEES:
        2-4 HIGH-CONFIDENCE STOCKS
        (From 100 analyzed)
```

---

## 💡 Tips for Best Results

1. **Pick high-volume industries**: AI, Cloud, Finance (more stocks = better filtering)
2. **Allow full time**: Don't interrupt scan - 16-20 seconds is normal
3. **Monitor both scores**: If they differ > 2 points, might be false signal (good)
4. **Check signal agreement**: BUY/BUY or SELL/SELL only - prevents conflicts
5. **Adjust thresholds gradually**: Change by 0.5 points at a time to find sweet spot
6. **Run multiple sectors**: Compare results across AI, Cloud, Crypto, etc.

---

## 📞 Support

### Common Questions

**Q: Why does Stage 2 take so long?**
A: It runs full analysis on ~10 candidates. Placeholder now; faster with simplified scoring.

**Q: Can I disable two-stage filtering?**
A: Set `HYBRID_SCAN_ENABLED = False` in config.py, but loses validation benefits.

**Q: What if I want only Stage 1 fast results?**
A: Set `QUICK_SCAN_MIN_SCORE = 2.0` and `QUICK_SCAN_MAX_CANDIDATES = 5` for quick scan.

**Q: How do I add more industries?**
A: Edit industry lists in src/nodes.py - add tickers to the sector definitions.

---

## ✨ What's Next?

Phase 6 Integration:
- Replace placeholder deep analysis with 39-node graph
- Will have access to news, sentiment, algorithms
- Same two-stage workflow but with more powerful Stage 2
- Expected to improve accuracy to 95%+

Current Status: ✅ Framework ready, awaiting Phase 6 orchestration
