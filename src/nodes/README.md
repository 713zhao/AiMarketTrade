# Nodes Package - Deerflow Trading System

## Overview

The `nodes` package contains the executable logic units (nodes) of the Deerflow trading graph. Each node performs a specific task in the trading workflow, reads/writes state, and communicates via the LangGraph framework.

**Design Principle:** Each node is focused, autonomous, and implements the `BaseNode` interface for consistency and error handling.

---

## Architecture

```
src/nodes/
├── base.py                    # Abstract BaseNode class and interface
├── data_node.py               # Phase 1: Market data fetching
├── analyst_nodes.py           # Phase 2: Six specialized analyst agents
├── consensus_node.py          # Phase 3: Signal aggregation and decision
├── portfolio_nodes.py         # Phase 4: Portfolio analysis and optimization
├── production_nodes.py        # Phase 5: Backtesting and production metrics
├── advanced_nodes.py          # Phase 7: Derivatives and complex strategies
└── __init__.py                # Node registry and exports
```

---

## Core Concept: The BaseNode Class

All nodes inherit from `BaseNode` which provides:

```python
class BaseNode:
    def __init__(self, node_id: str):
        """Initialize with unique node identifier."""
        self.node_id = node_id
        self.settings = get_settings()
    
    async def execute(self, state: DeerflowState) -> DeerflowState:
        """Main entry point - handles error handling and state updates."""
        try:
            state = await self._execute(state)
            state.completed_nodes.append(self.node_id)
        except Exception as e:
            state.add_error(self.node_id, str(e))
            raise
        finally:
            state.update_timestamp()
        return state
    
    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Subclass implements actual logic here."""
        raise NotImplementedError()
```

**Features:**
- ✅ Automatic error handling and logging
- ✅ State tracking (which nodes completed)
- ✅ Timestamp updates
- ✅ Exception propagation

---

## Node Modules by Phase

### 1. **base.py** - The Foundation
**File Size:** Core interface definitions

**Classes:**
- `BaseNode` - Abstract base for all nodes
- `NodeResult` - TypedDict for node output

**Key Concepts:**
- Every node has a unique `node_id`
- Nodes are async (use `async`/`await`)
- Nodes are pure functions: `DeerflowState → DeerflowState`
- Errors are captured in state, not raised to caller

---

### 2. **data_node.py** - Phase 1: Data Collection
**File Size:** ~200 lines
**Responsibility:** Fetch market data from OpenBB

**Node:**
| Node | Input | Output | Purpose |
|------|-------|--------|---------|
| `StockDataNode` | tickers list | TickerData dict | Fetch OHLC, fundamentals, news |

**Data Sources:**
- Historical OHLC prices
- Company fundamentals (PE ratio, dividend yield, etc.)
- Financial statements (income, balance sheet, cash flow)
- News and events

**Features:**
- Multi-provider fallback (FMP → Polygon → Yahoo)
- Data quality scoring
- Error handling per ticker (partial failures okay)
- Async concurrent fetching

**Usage in Graph:**
```python
# Phase 1: Collect data
state = await StockDataNode().execute(state)
# Now state.ticker_data has all market data
```

---

### 3. **analyst_nodes.py** - Phase 2: Six Specialists
**File Size:** ~400 lines
**Responsibility:** Parallel analyst agents providing diverse perspectives

**Nodes:**

| Node | Analyzes | Output Model | Metrics |
|------|----------|--------------|---------|
| `TechnicalAnalystNode` | Price action, volume | TechnicalAnalysis | RSI, MACD, Bollinger Bands |
| `FundamentalsAnalystNode` | Company financials | FundamentalAnalysis | P/E, dividend yield, growth |
| `NewsAnalystNode` | Market news, sentiment | NewsAnalysis | Sentiment score, catalysts |
| `GrowthAnalystNode` | Long-term growth potential | GrowthAnalysis | Growth rate, CAGR projections |
| `RiskAnalystNode` | Risk metrics and exposure | RiskAnalysis | Beta, VaR, standard deviation |
| `MacroAnalystNode` | Economic factors | MacroAnalysis | GDPgrowth, inflation, rates |

**Design Pattern:**
```
Each analyst node:
1. Reads TickerData (Phase 1 output)
2. Performs specialized analysis
3. Writes to state (e.g., state.technical_analysis = ...)
4. Returns modified state
```

**Parallelization:**
All 6 analysts can run in parallel in the graph:
```python
# Graph structure: All run simultaneously
state = await asyncio.gather(
    TechnicalAnalystNode().execute(state),
    FundamentalsAnalystNode().execute(state),
    NewsAnalystNode().execute(state),
    # ... etc
)
```

**Error Tolerance:**
- If any analyst fails, state captures error but continues
- ConsensusNode weights successful analysts higher

---

### 4. **consensus_node.py** - Phase 3: Aggregation & Decision
**File Size:** ~300 lines
**Responsibility:** Aggregate analyst signals into actionable decision

**Nodes:**

| Node | Inputs | Output | Purpose |
|------|--------|--------|---------|
| `ConsensusNode` | 6 analyst results | ConsensusSignal | Aggregate signals with weights |
| `DecisionNode` | ConsensusSignal | TradingDecision | Final BUY/SELL/HOLD decision |

**ConsensusNode Logic:**
1. Collects all 6 analyst opinions
2. Calculates agreement level (how many analysts agree)
3. Weights signals by analyst type (some more trusted)
4. Outputs ConsensusSignal with confidence scores

**DecisionNode Logic:**
1. Reads ConsensusSignal
2. Applies thresholds (min agreement, min confidence)
3. Determines action: BUY / SELL / HOLD
4. Sets position size: small / medium / large
5. Suggests entry/exit prices

**Decision Matrix:**
```
Agreement | Confidence | Signal    | Action | Size
----------|------------|-----------|--------|-------
    high  |    high    | positive  | BUY    | LARGE
    high  |    high    | negative  | SELL   | LARGE
    high  |    medium  | positive  | BUY    | MEDIUM
    low   |    any     | any       | HOLD   | NONE
```

---

### 5. **portfolio_nodes.py** - Phase 4: Portfolio Optimization
**File Size:** ~350 lines
**Responsibility:** Optimize portfolio allocation and manage risk

**Nodes:**

| Node | Purpose | Algorithm |
|------|---------|-----------|
| `PortfolioRiskNode` | Compute portfolio-level risk | Portfolio variance, correlation |
| `PortfolioOptimizationNode` | Optimal allocation | Mean-variance optimization |
| `MacroScenarioNode` | Model macro scenarios | Bull/bear/sideways cases |
| `MultiScenarioAnalysisNode` | Stress test portfolio | Returns across scenarios |
| `RebalancingNode` | Rebalancing strategy | Drift thresholds, frequency |

**PortfolioOptimizationNode:**
- Inputs: Individual position recommendations
- Algorithm: Modern Portfolio Theory (MPT)
- Outputs: Optimal portfolio weights minimizing risk for target return
- Constraints:
  - Min/max position size limits
  - Sector concentration limits
  - Portfolio volatility target

**MacroScenarioNode:**
- Models 3-5 macro scenarios:
  - **Bull**: High growth, low rates, risk-on
  - **Bear**: Recession fears, rising rates, deleveraging
  - **Sideways**: Choppy, range-bound
  - **Inflation Spike**: Stagflation concerns
  - **Deflationary**: Credit crunch fears

- For each scenario, estimates:
  - Expected returns per asset
  - Volatility increase
  - Correlation changes

---

### 6. **production_nodes.py** - Phase 5: Backtesting & Metrics
**File Size:** ~400 lines
**Responsibility:** Historical validation and production readiness

**Nodes:**

| Node | Purpose | Output |
|------|---------|--------|
| `EfficientFrontierNode` | Compute frontier | EfficientFrontierData |
| `PerformanceAttributionNode` | Explain returns | Performance breakdown by position |
| `TransactionCostNode` | Estimate trading costs | Commission, slippage, bid-ask |
| `BacktestingEngineNode` | Historical simulation | BacktestResult with metrics |

**BacktestingEngineNode:**
1. Inputs: Portfolio definition, trading signals, start-end dates
2. Simulation loop:
   - For each day/period:
     - Apply market returns
     - Rebalance if signals trigger
     - Calculate transaction costs
     - Update metrics
3. Outputs:
   - Total return %
   - Sharpe ratio
   - Max drawdown
   - Win rate
   - Profit factor

**EfficientFrontierNode:**
1. Computes return/risk for different allocation weights
2. Finds frontier curve (Pareto-optimal portfolios)
3. Identifies:
   - Maximum Sharpe ratio portfolio (best risk-adjusted return)
   - Minimum variance portfolio (lowest risk)
   - Various return targets along frontier

---

### 7. **advanced_nodes.py** - Phase 7: Derivatives & Complex Strategies
**File Size:** ~500 lines
**Responsibility:** Advanced instruments and sophisticated strategies

**Nodes:**

| Node | Purpose | Handles |
|------|---------|---------|
| `OptionsAnalysisNode` | Options strategy analysis | Calls, puts, spreads, straddles |
| `FuturesAnalysisNode` | Futures opportunities | Short-dated, roll strategy |
| `CryptoDerivativesNode` | Perpetual/crypto futures | Leverage, liquidation risk |
| `StrategyBuilderNode` | Construct complex strategies | Multi-leg optimization |
| `GreeksMonitorNode` | Monitor Greek exposure | Delta, gamma, vega limits |
| `DeltaHedgingNode` | Automatic hedging | Maintain delta neutrality |
| `HedgeRecommenderNode` | Suggest hedges | Tail risk mitigation |

**GreeksCalculator:**
```
Calculate Greeks (risk sensitivities):
- Delta: Price sensitivity
- Gamma: Delta sensitivity (convexity)
- Vega: Volatility sensitivity
- Theta: Time decay
- Rho: Interest rate sensitivity
```

**StrategyBuilder:**
Common strategies:
- **Vertical Spread** - Different strike prices, same expiration
- **Calendar Spread** - Different expirations, same strike
- **Straddle** - Long call + long put (volatility bet)
- **Strangle** - Out-of-money straddle
- **Ratio Spread** - Asymmetric legs

**DeltaHedging:**
- Monitors portfolio delta continuously
- Automatically adds/removes hedges to maintain delta ≈ 0
- Trades when delta drifts beyond thresholds

---

## Execution Flow

```
Phase 1: Data Collection
├── StockDataNode
│   └─→ TickerData collected

Phase 2: Multi-Analyst Analysis (Parallel)
├── TechnicalAnalystNode ───────┐
├── FundamentalsAnalystNode ───┤
├── NewsAnalystNode ───────────┤
├── GrowthAnalystNode ────────┤
├── RiskAnalystNode ─────────┤
└── MacroAnalystNode ────────┴─→ ConsensusNode

Phase 3: Consensus & Decision
├── ConsensusNode ──→ Aggregated signal
└── DecisionNode ───→ TradingDecision

Phase 4: Portfolio Optimization
├── PortfolioRiskNode ──┐
├── MacroScenarioNode ──┼─→ PortfolioOptimizationNode
├── MultiScenarioAnalysisNode ┤
└── RebalancingNode ────┘

Phase 5: Production Readiness
├── BacktestingEngineNode ──→ Historical validation
├── EfficientFrontierNode ──→ Frontier optimization
├── PerformanceAttributionNode ──→ Return attribution
└── TransactionCostNode ────→ Cost analysis

Phase 6: Broker Integration (Not nodes)
└── Orders executed via broker adapters

Phase 7: Advanced Strategies (Optional)
├── OptionsAnalysisNode ────┐
├── FuturesAnalysisNode ────┼─→ StrategyBuilderNode
├── CryptoDerivativesNode ──┤
└── GreeksMonitorNode ───┬──┴──→ HedgeRecommenderNode
                         │
                    DeltaHedgingNode (continuous)
```

---

## Common Node Patterns

### Pattern 1: Simple Transformation
```python
class MyAnalysisNode(BaseNode):
    def __init__(self):
        super().__init__("my_analysis_node")
    
    async def _execute(self, state: DeerflowState) -> DeerflowState:
        # Read input
        if state.ticker_data is None:
            raise ValueError("TickerData required")
        
        # Process
        analysis = perform_analysis(state.ticker_data)
        
        # Write output
        state.my_analysis = analysis
        
        return state
```

### Pattern 2: Conditional Execution
```python
async def _execute(self, state: DeerflowState) -> DeerflowState:
    # Check prerequisites
    if not self.should_process(state):
        self.log("Skipping - prerequisites not met")
        return state
    
    # Process
    result = await self.compute(state)
    state.result = result
    
    return state
```

### Pattern 3: Error Tolerance
```python
async def _execute(self, state: DeerflowState) -> DeerflowState:
    for ticker in state.tickers:
        try:
            result = compute(ticker)
            state.results[ticker] = result
        except Exception as e:
            state.add_error(self.node_id, f"Failed {ticker}: {e}")
            # Continue processing other tickers
    
    return state  # Partial success is okay
```

---

## Testing Nodes

Each node has corresponding tests in `tests/`:

```bash
# Test individual node
pytest tests/test_nodes.py::TestStockDataNode -v

# Test all analyst nodes
pytest tests/test_nodes.py::TestAnalystNodes -v

# Test node integration in graph
pytest tests/test_integration.py -v
```

---

## Best Practices

1. **Always Call Super Init**
   ```python
   def __init__(self):
       super().__init__("unique_node_id")
   ```

2. **Validate Prerequisites**
   ```python
   if state.ticker_data is None:
       raise ValueError("TickerData required")
   ```

3. **Use Logging** (via base class)
   ```python
   self.log(f"Processing {len(state.tickers)} tickers")
   ```

4. **Handle Errors Gracefully**
   ```python
   try:
       result = compute(data)
   except Exception as e:
       state.add_error(self.node_id, str(e))
       # Continue or return partial state
   ```

5. **Return Modified State**
   ```python
   # Always return state (or modified version)
   return state
   ```

6. **Use Type Hints**
   ```python
   async def _execute(self, state: DeerflowState) -> DeerflowState:
       pass
   ```

---

## Debugging Nodes

### Check Node Execution Order
```python
# Which nodes completed?
print(state.completed_nodes)  # ['stock_data_node', 'technical_analyst', ...]
```

### Check Node Errors
```python
# What errors occurred?
print(state.errors)  # {'stock_data_node': 'API timeout', ...}
```

### Add Debug Logging
```python
self.log(f"Debug info: {var}", "DEBUG")
# Check logs in output
```

---

## Future Node Ideas

- **NewsNLPNode** - Deep NLP sentiment analysis
- **MLPredictorNode** - Machine learning forecasts
- **RealTimeMonitorNode** - Live market monitoring
- **AlertingNode** - Threshold-based alerts
- **IterativeOptimizerNode** - Reinforcement learning optimization

---

## Performance Tuning

### Parallel Execution
Nodes in Phase 2 (analysts) run in parallel via LangGraph:
```python
# Graph config
parallel=True
```

### Async I/O
All I/O operations are async (OpenBB API calls, database queries):
```python
async def _fetch_data(self, ticker):
    # Non-blocking API call
    return await obb.stock.historical(ticker)
```

### Caching
Use `@lru_cache` for expensive computations:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def compute_expensive_metric(ticker):
    # Only compute once per unique ticker
    pass
```

---

## Summary

| Phase | Nodes | Purpose | Input | Output |
|-------|-------|---------|-------|--------|
| 1 | StockDataNode | Data collection | Tickers | TickerData |
| 2 | 6 Analysts | Specialized analysis | TickerData | Analyst results |
| 3 | 2 Consensus | Aggregation | Analyst results | TradingDecision |
| 4 | 5 Portfolio | Optimization | Decisions | Portfolio allocation |
| 5 | 4 Production | Backtesting & metrics | Portfolio | BacktestResult |
| 6 | Broker API | Execution (not nodes) | Portfolio | Filled orders |
| 7 | 7 Advanced | Derivatives | Portfolio | Hedge recommendations |

