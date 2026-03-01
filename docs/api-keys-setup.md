# API Keys Setup Guide for Deerflow + OpenBB

## Getting Free API Keys

This guide helps you obtain free API keys for the deerflow-openbb system.

## Recommended: Start with Yahoo Finance (No API Key Required)

Yahoo Finance is built into OpenBB via yfinance and **requires no API key** for basic market data.

```bash
# You can immediately run:
python -m deerflow_openbb --mode mock AAPL  # With mock data
# OR if yfinance works:
python -m deerflow_openbb AAPL --mode auto   # Tries Yahoo first
```

Yahoo Finance provides:
- ✅ Historical prices (up to 2 years)
- ✅ Basic company info
- ✅ Limited news
- ❌ No fundamentals (financial statements)
- ❌ No real-time data
- ❌ Limited option chain

## For Enhanced Data: Get a Free Financial Modeling Prep (FMP) Key

FMP is **the recommended provider** for deerflow because it offers:

- ✅ All Yahoo Finance features **plus**
- ✅ Complete financial statements (income, balance, cash flow)
- ✅ Fundamental ratios (P/E, P/B, ROE, etc.)
- ✅ Company news and sentiment
- ✅ Analyst estimates
- ✅ Screening data
- ⚠️ Rate limits: 250 requests/day (free tier)

**Get your free FMP API key:**

1. Go to https://financialmodelingprep.com/developer/docs/
2. Click "Get Started" or "Sign Up"
3. Register with email
4. Once logged in, go to your **Account Settings** or **API Key** page
5. Copy your API key (starts with a long alphanumeric string)
6. Add to `.env`:
   ```bash
   FMP_API_KEY=your_key_here
   ```

**Verify:**
```bash
python -c "from openbb import obb; print(obb.equity.price.historical('AAPL', provider='fmp').head())"
```

## Alternative: Polygon.io (Real-Time Data)

Polygon provides excellent real-time and historical data.

- ✅ Real-time stock quotes
- ✅ Historical OHLC (intraday, daily)
- ✅ Options, crypto, forex
- ✅ Good fundamentals
- ❌ Free tier: 5 API calls/minute, limited endpoints
- ❌ Requires credit card for free tier signup

**Get Polygon API key:**

1. Go to https://polygon.io/
2. Click "Get Started" → "Start for Free"
3. Sign up (requires credit card verification, but free tier is free)
4. API key in dashboard: https://polygon.io/dashboard/api-keys
5. Add to `.env`:
   ```bash
   POLYGON_API_KEY=your_key_here
   ```

## For Without Credit Card: Alpha Vantage

Alpha Vantage offers a generous free tier without credit card requirement.

- ✅ Stock prices (daily, intraday)
- ✅ Forex, crypto
- ✅ Technical indicators
- ✅ Limited fundamentals
- ⚠️ Rate limits: 5 calls/minute, 500/day
- ❌ No company news

**Get Alpha Vantage API key:**

1. Go to https://www.alphavantage.co/
2. Click "Get Your Free API Key Today"
3. Fill in the form (use any email)
4. Check your email for the API key
5. Add to `.env`:
   ```bash
   ALPHA_VANTAGE_API_KEY=your_key_here
   ```

## Optional: For Better News - Benzinga

If you want high-quality financial news:

1. Go to https://www.benzinga.com/apis
2. Click "Get Started Free"
3. Register and get API key
4. Add to `.env`:
   ```bash
   BENZINGA_API_KEY=your_key_here
   ```

Note: Benzinga free tier is very limited (25 calls/day).

---

## Complete `.env` Example

Here's a sample `.env` file with all keys configured:

```bash
# Data Providers (pick at least one)
FMP_API_KEY=abc123def456...         # Best for fundamentals (get this!)
# POLYGON_API_KEY=poly_key_123...   # Good for real-time (requires CC)
# ALPHA_VANTAGE_API_KEY=AV_key...   # No credit card needed
# BENZINGA_API_KEY=benzinga_key...  # For premium news (optional)

# LLM Provider (for analysis reasoning)
OPENAI_API_KEY=sk-proj-...          # OpenAI GPT-4
# OR
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic Claude

# Optional Configuration
DEFAULT_TICKERS=AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,JPM,JNJ,V
DEFAULT_LLM_MODEL=gpt-4
LOG_LEVEL=INFO
MAX_POSITION_SIZE=5.0
```

---

## Verifying Your Setup

### Step 1: Create `.env` file
```bash
cd /home/node/.openclaw/workspace/deerflow-openbb
cp .env.template .env
# Edit .env with your API keys
```

### Step 2: Check Configuration
```bash
python -m deerflow_openbb --check-config
```

Expected output:
```
Configuration Validation
--------------------------------------------------
Primary data provider: fmp
  ✓ API key configured for fmp
✓ OpenAI API key configured (model: gpt-4)

Available data providers:
  ✓ fmp
  ✓ yahoo
```

If you see "WARNING: FMP_API_KEY not configured!", edit `.env` and add your key.

### Step 3: Test Data Access
```bash
# With mock mode (always works)
python -m deerflow_openbb --mode mock AAPL

# With live data (requires FMP or other provider)
python -m deerflow_openbb --mode auto AAPL
```

If live mode fails:
1. Check API key is in `.env` (no quotes, no spaces)
2. Ensure FMP provider is selected: `--provider fmp`
3. Verify API key works: `python -c "from openbb import obb; print(obb.equity.price.historical('AAPL', provider='fmp'))"`
4. If error: "Invalid API key" → get new key from FMP dashboard

---

## Troubleshooting

### "API key not configured" even though I set it

- Check: Don't put quotes around values
  ```bash
  # Good
  FMP_API_KEY=abc123

  # Bad (includes quotes as part of key)
  FMP_API_KEY="abc123"
  ```
- No spaces after `=`
- Verify `.env` is in project root (where `pyproject.toml` is)
- Run `python -m deerflow_openbb --check-config` to debug

### "rate limit exceeded" from FMP

- Free tier: 250 requests/day
- Solution: Add `POLYGON_API_KEY` or `YAHOO` as fallback
- Config auto-rotates through available providers

### "Invalid API key" from provider

- Copy key from FMP dashboard carefully (it's long)
- Generate new key if unsure
- FMP keys look like: `XoXoXoXoXoXoXoXoXoXoXoXoXoXoXoX`

### Module import errors (No module named 'pydantic')

- Run: `pip3 install -e ".[dev]"`
- If permission denied: `pip3 install --user -e ".[dev]"`
- Or create venv: `python3 -m venv venv && source venv/bin/activate && pip install -e ".[dev]"`

---

## Provider Comparison

| Feature | Yahoo | FMP (Free) | Polygon (Free) | Alpha Vantage (Free) |
|---------|-------|------------|----------------|---------------------|
| Price data | ✅ 2yr daily | ✅ Full history | ✅ Intraday+ | ✅ Daily+ |
| Real-time | ❌ | ❌ | ✅ | ❌ |
| Fundamentals | ❌ | ✅ | ✅ | ⚠️ Limited |
| Financials | ❌ | ✅ | ✅ | ❌ |
| News | ⚠️ Limited | ✅ | ✅ | ❌ |
| Rate limit | None | 250/day | 5/min | 5/min |
| API key | ❌ No | ✅ Free | ✅ Free | ✅ Free |
| CC required? | N/A | ❌ No | ✅ Yes | ❌ No |

**Recommendation**: Get FMP key (250 calls/day is plenty for personal use)

---

## Cost & Usage Notes

- All recommended providers have **free tiers** sufficient for testing and light use
- For production/automated trading, consider paid plans ($19-199/mo)
- OpenAI/Anthropic API costs: ~$0.01-0.10 per analysis (very affordable)
- Always monitor API usage in provider dashboards

---

## Security Best Practices

1. **Never commit `.env` to git** (it's in `.gitignore`)
2. **Rotate keys periodically** (especially if sharing code)
3. **Use environment-specific keys** (dev vs prod)
4. **Monitor API usage** for anomalies
5. **Don't share your keys** in screenshots or logs

---

## Getting Help

- **OpenBB Docs**: https://docs.openbb.co/
- **FMP Support**: https://financialmodelingprep.com/developer/docs/help
- **Issues**: Check GitHub issues or create one

---

**Last Updated**: 2026-03-01
**Required for**: Phase 1+ live data analysis
**Minimum**: FMP_API_KEY (strongly recommended)
