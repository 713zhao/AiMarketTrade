# Deerflow + OpenBB Trading System

[![Phase 2](https://img.shields.io/badge/Phase-2%20Multi--Agent%20Expansion-blue)](https://deerflow-openbb.readthedocs.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready multi-agent trading system that combines [deerflow's](https://github.com/hetaoBackend/deer-trade) LangGraph-based orchestration architecture with [OpenBB's](https://openbb.co) comprehensive financial data platform.

**Current Version**: 0.2.0 (Phase 2 - Multi-Agent Expansion)
**Status**: Ready for Testing and Evaluation

## Key Feature: Parallel Analyst Execution

Phase 2 implements **6 specialized analyst agents** running in parallel:

1. **Technical Analyst** - Price patterns, indicators, signals
2. **Fundamentals Analyst** - Financial health, valuation ratios
3. **Growth Analyst** - Future potential, revenue/EPS growth
4. **News Analyst** - Sentiment analysis, catalyst detection
5. **Macro Analyst** - Economic context, sector trends
6. **Risk Analyst** - Volatility, drawdown, financial risk

All analysts contribute to a **consensus signal**, which produces final trading decisions with comprehensive rationale.

## Architecture

```
Data Fetch (StockDataNode)
         |
         v
    +----+----+------------------+
    |         |                  |
    v         v                  v
Tech      Fundamentals       News Analyst
|             |                  |
v             v                  |
Growth       Macro               |
 |             |                  |
 +-------------+                  |
               |                  |
            Risk Analyst ----+
                    |
                    v
               Consensus
                    |
                    v
                 Decision
                    |
                    v
                 Output
```

## Features

- **Multi-Agent Architecture**: 6 specialized analysts working in parallel
- **Consensus Engine**: Weighted aggregation of all analyst signals
- **OpenBB Integration**: Direct Python SDK access to 20+ data providers
- **State-Based Workflow**: Type-safe state management with Pydantic
- **Parallel Execution**: All analysts run concurrently for speed
- **Comprehensive Rationale**: Human-readable explanation of decisions
- **Risk Management**: Volatility-based stops, position sizing
- **Mock Mode**: Test without API keys using synthetic data
- **Multiple Outputs**: summary, JSON, CSV formats

## Quick Start

### 1. Install Dependencies

```bash
cd /home/node/.openclaw/workspace/deerflow-openbb
pip3 install -e ".[dev]"
```

### 2. Configure (Optional - Mock Mode Works Without Keys)

```bash
cp .env.template .env
# Edit .env and add API keys (recommended: FMP_API_KEY for fundamentals)
```

**Note**: Yahoo Finance is available without API keys. For full analysis, get a free [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs/) API key (250 calls/day free).

### 3. Run Analysis

```bash
# Test with mock data (no API keys required)
python -m deerflow_openbb --mode mock AAPL

# Live analysis (requires API keys)
python -m deerflow_openbb --mode auto AAPL MSFT GOOGL

# With options
python -m deerflow_openbb --tickers AAPL,AMZN,NVDA --output json --output-file results.json

# Check configuration
python -m deerflow_openbb --check-config
```

## Command-Line Options

```bash
--mode {live,mock,auto}   # Data source (default: auto)
--tickers TICKERS         # Comma-separated tickers or positional
--output {summary,json,csv,silent}  # Output format (default: summary)
--output-file FILE        # Write to file instead of stdout
--full-pipeline          # Force all 6 analysts (default in Phase 2)
--check-config           # Validate configuration and exit
--verbose, -v            # Verbose logging
```

## Output Interpretation

### Summary Output (Default)

```
DEERFLOW ANALYSIS SUMMARY
==================================================

AAPL:
  Data Quality: 92%
  Technical: Trend=bullish, Momentum=oversold, Confidence=78%
    Signals: 3 buy, 1 sell
  Fundamental: Valuation=fair, PE=28.5, ROE=21.3%
  News: Sentiment=+0.42, Volume=15 articles
  Growth: Score=72/100, Revenue Growth=8.5%
  Risk: Level=medium, Volatility=22%
  Macro: Score=58/100, Sector=Technology
  Consensus: BUY (strength: 68%) Confidence: 74%
    Technical: +0.42 (w=0.20) 看多
    Fundamentals: +0.28 (w=0.25) 看多
    News: +0.35 (w=0.15) 看多
    Growth: +0.18 (w=0.15) 看多
    Risk: -0.12 (w=-0.15) 中性
    Macro: +0.05 (w=0.10) 中性
  Decision: BUY - 3.2% position
    Stop: $175.50, Target: $195.00
    Rationale: 综合分析给出买入建议，强度68%，可信度74%...
```

### JSON Output

```json
{
  "session_id": "abc-123",
  "tickers": ["AAPL"],
  "execution_time": 45.2,
  "consensus_signals": {
    "AAPL": {
      "overall_signal": "buy",
      "signal_strength": 0.68,
      "consensus_confidence": 0.74,
      "analyst_signals": {
        "technical": {"score": 0.42, "weight": 0.2, "confidence": 0.78},
        "fundamentals": {"score": 0.28, "weight": 0.25, "confidence": 0.65},
        ...
      }
    }
  },
  "trading_decisions": {
    "AAPL": {
      "action": "buy",
      "position_size": 3.2,
      "stop_loss": 175.5,
      "take_profit": 195.0,
      "confidence": 0.74,
      "rationale": "综合分析给出买入建议..."
    }
  }
}
```

## Analyst Details

### Technical Analyst
- **Indicators**: SMA-20/50/200, EMA-12/26, RSI-14, MACD, Bollinger Bands, ATR-14
- **Signals**: Golden/Death cross, RSI extremes, MACD crossovers, Bollinger touches
- **Output**: trend, momentum, support/resistance levels, confidence

### Fundamentals Analyst
- **Metrics**: P/E, P/B, P/S, PEG, ROE, ROA, margins, debt/equity, current ratio
- **Valuation**: Undervalued/Fair/Overvalued assessment
- **Output**: strengths, weaknesses, fair value estimate

### Growth Analyst
- **Growth Rates**: Revenue CAGR, EPS growth, R&D intensity
- **Estimates**: Next quarter/year, long-term growth
- **Output**: growth_score (0-100), trend (accelerating/stable/decelerating)

### News Analyst
- **Sentiment**: Rule-based scoring (-1 to +1) across all articles
- **Catalysts**: Earnings, products, M&A, regulation, legal, management
- **Risk Events**: Negative news identification
- **Output**: overall_sentiment, news_volume, catalysts, confidence

### Risk Analyst
- **Volatility**: Annualized from daily returns
- **VaR/CVaR**: 95% Value at Risk
- **Drawdown**: Max and current
- **Beta**: Relative to market
- **Financial Risk**: Debt ratios, interest coverage, liquidity
- **Output**: risk_score (0-100), risk_level (low/medium/high)

### Macro Analyst
- **Environment**: Interest rates, inflation, GDP, unemployment
- **Sector Context**: Rotation trends, regulatory factors
- **Output**: macro_score, sector, economic outlook

## Consensus Engine

Combines all analyst signals using configurable weights:

```python
weights = {
    Technical: 20%,
    Fundamentals: 25%,
    News: 15%,
    Growth: 15%,
    Risk: -15%,  # Negative: higher risk reduces buy signal
    Macro: 10%
}
```

Each analyst's signal is normalized to [-1, +1], weighted by confidence, and aggregated to produce final signal.

## Configuration

See `.env.template` for all options. Key settings:

```bash
# Data provider (auto-detected, priority: fmp > polygon > yahoo)
FMP_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here

# LLM for enhanced analysis (optional - rule-based works too)
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# Trading parameters
DEFAULT_TICKERS=AAPL,MSFT,GOOGL,AMZN,NVDA
MAX_POSITION_SIZE=5.0
DEFAULT_LLM_MODEL=gpt-4
LOG_LEVEL=INFO
```

## Testing

```bash
# Validate installation
python3 validate.py

# Check configuration
python -m deerflow_openbb --check-config

# Test with mock data (no API keys)
python -m deerflow_openbb --mode mock AAPL

# Run unit tests (after pip install)
pytest tests/ -v

# Run integration test directly
python tests/test_integration.py
```

## Project Structure

```
deerflow-openbb/
├── src/
│   ├── config.py         # Settings & environment
│   ├── state.py          # Pydantic state schemas
│   ├── nodes.py          # All node implementations (6 analysts + consensus + decision)
│   ├── graph.py          # LangGraph orchestration with parallel execution
│   └── main.py           # CLI entry point
├── tests/
│   ├── test_config.py
│   ├── test_state.py
│   ├── test_nodes.py
│   └── test_integration.py
├── docs/
│   ├── phase2-summary.md
│   └── api-keys-setup.md
├── pyproject.toml
├── .env.template
├── README.md
└── validate.py
```

## Technical Details

### Dependencies

- **Core**: openbb[all] (4.2+), langgraph (0.0.20+), pydantic (2.0+)
- **Data**: numpy, pandas, ta (technical analysis)
- **Dev**: pytest, black, ruff, mypy

### State Schema

All data flows through `DeerflowState` (see `src/state.py`):

- `TickerData`: Raw market data from OpenBB
- 7 Analysis types: Technical, Fundamental, News, Growth, Macro, Risk, Consensus
- `TradingDecision`: Final output with position sizing, stops, rationale

### Parallel Execution

LangGraph automatically parallelizes independent nodes. After `stock_data`, all 6 analyst nodes execute concurrently, then join at `consensus`, then `decision`.

### Error Resilience

Each node catches exceptions and logs to `state.errors`. The graph continues running even if some analysts fail, allowing partial analysis.

### Mock Data

`MockStockDataNode` generates realistic synthetic data with:
- Realistic price paths (lognormal random walk)
- Parametrized fundamental metrics
- Sector diversity
- Consistent data quality

Perfect for development and testing without API keys.

## FAQ

### Q: How many API calls does this make?
A: Phase 2 makes ~50-100 calls per ticker (varies by provider). FMP free tier allows 250/day. For 5 tickers, you'll need ~500 calls - consider paid plan or use multiple keys.

### Q: How long does analysis take?
A: With live data: 30-90 seconds for 5 tickers. Mock data: 1-3 seconds.

### Q: Can I add my own analyst?
A: Yes! Create a new node extending `BaseNode`, implement `_execute`, and register in `graph.py`.

### Q: Why are some analyses missing?
A: Analysts gracefully skip if data unavailable (e.g., fundamentals if provider doesn't support it). Consensus weights adjust based on available analysts.

### Q: Is this production-ready?
A: Phase 2 is testing-ready but not production-hardened. Complete through Phase 5 for production deployment with monitoring, alerting, and risk limits.

## Implementation Roadmap

- **Phase 1**: Foundation ✅ (Completed)
  - Basic pipeline, technical analysis, data infrastructure

- **Phase 2: Multi-Agent Expansion** ✅ (Completed - Current)
  - All 6 analyst nodes implemented
  - Parallel execution
  - Consensus aggregation

- **Phase 3**: Risk & Decision Engine
  - Advanced risk models (Monte Carlo, stress testing)
  - Portfolio optimization
  - Dynamic position sizing

- **Phase 4**: Trading Integration
  - Broker connectivity (Alpaca, Interactive Brokers)
  - Paper trading simulation
  - Order management

- **Phase 5**: Production Readiness
  - Redis caching, rate limiting
  - Comprehensive monitoring
  - Security hardening

- **Phase 6**: Advanced Features
  - Self-improvement (backtest → refine)
  - Alternative data (options flow, insider trades)
  - Machine learning models
  - Real-time streaming

## Contributing

This is a solo implementation. Suggestions welcome via issues.

## Disclaimer

**For educational and research purposes only.** Not financial advice. Trading involves significant risk. Always conduct your own research and consult a qualified financial advisor before making investment decisions.

---

Built with deerflow architecture and OpenBB platform.