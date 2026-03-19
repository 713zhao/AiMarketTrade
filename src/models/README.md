# Models Package - Deerflow Trading System

## Overview

The `models` package organizes all data structures and types used throughout the Deerflow trading system. It replaces the legacy monolithic `state.py` with a **phase-aligned, modular architecture** that clearly separates concerns across the 7 trading phases.

**Key Principle:** Models are organized by trading phase, making it easy to understand what data flows through each phase of the system.

---

## Architecture

```
src/models/
├── base.py                    # Core enumerations and types
├── ticker_models.py           # Phase 1-2: Data collection and technical analysis
├── analysis_models.py         # Phase 2-3: Multi-analyst consensus and decisions
├── portfolio_models.py        # Phase 3-4: Portfolio optimization and risk analysis
├── production_models.py       # Phase 5: Backtesting and production deployment
├── broker_models.py           # Phase 6: Broker API integration and order execution
├── advanced_models.py         # Phase 7: Derivatives and complex strategies
├── deerflow_state.py          # Master state object integrating all phases
└── __init__.py                # Public API exports for backward compatibility
```

---

## Module Details

### 1. **base.py** (1.4 KB)
**Purpose:** Shared enumeration types used throughout the system

**Enums:**
- `AnalystType` - Types of analyst agents (NEWS, TECHNICAL, FUNDAMENTALS, GROWTH, MACRO, RISK, PORTFOLIO, etc.)
- `SignalType` - Trading signals (BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL)
- `DataProvider` - Data providers (FMP, POLYGON, YAHOO, ALPHA_VANTAGE, EODHD)
- `MarketRegime` - Market conditions (BULL, BEAR, SIDEWAYS, HIGH_VOLATILITY, LOW_VOLATILITY, TRANSITION)

**When to use:**
- Whenever you need type-safe enumerations instead of magic strings
- For analyst type identification throughout the system
- For signal direction and data provider references

---

### 2. **ticker_models.py** (6.3 KB)
**Purpose:** Phase 1-2 raw market data and initial technical analysis

**Classes:**
| Class | Purpose | Key Fields |
|-------|---------|-----------|
| `TickerData` | Raw market data for a ticker | historical_prices, fundamentals, news_items |
| `TechnicalAnalysis` | Technical indicators and patterns | rsi, macd, bollinger_bands, patterns |
| `FundamentalAnalysis` | Company valuation and metrics | pe_ratio, dividend_yield, revenue |
| `NewsAnalysis` | News sentiment and impact | sentiment_score, catalyst_type, impact |

**Data Flow:**
1. **Phase 1** - DataNode collects raw ticker data
2. **Phase 2** - AnalystNodes compute technical and fundamental analysis
3. Output feeds into analysis_models.py for consensus

**Usage Example:**
```python
from src.models import TickerData, TechnicalAnalysis

ticker = TickerData(
    symbol="AAPL",
    historical_prices=[...],
    fundamentals={...},
    news_items=[...]
)

tech = TechnicalAnalysis(
    rsi=65.5,
    macd_signal="positive",
    patterns=["golden_cross"]
)
```

---

### 3. **analysis_models.py** (7.9 KB)
**Purpose:** Phase 2-3 multi-analyst consensus and trading decisions

**Classes:**
| Class | Purpose | Phase |
|-------|---------|-------|
| `GrowthAnalysis` | Growth potential assessment | 2-3 |
| `RiskAnalysis` | Risk evaluation | 2-3 |
| `MacroAnalysis` | Macroeconomic factors | 2-3 |
| `ConsensusSignal` | Aggregated signals from multiple analysts | 3 |
| `TradingDecision` | Final trading recommendation | 3 |
| `ScenarioAnalysis` | Multiple scenario outcomes | 3 |

**Data Flow:**
1. **Phase 1-2** - Individual analysts produce GrowthAnalysis, RiskAnalysis, MacroAnalysis
2. **Phase 3** - ConsensusNode aggregates into ConsensusSignal
3. **Phase 3** - Decision logic produces TradingDecision
4. Output feeds into portfolio_models.py for position sizing

**Usage Example:**
```python
from src.models import ConsensusSignal, TradingDecision

consensus = ConsensusSignal(
    analysts_results=[...],
    signal_strength=0.85,
    agreement_level=0.92
)

decision = TradingDecision(
    action="BUY",
    confidence=0.85,
    position_size="medium",
    entry_price=150.00
)
```

---

### 4. **portfolio_models.py** (10.2 KB)
**Purpose:** Phase 3-4 portfolio-level risk and optimization

**Classes:**
| Class | Purpose | Phase |
|-------|---------|-------|
| `PortfolioRiskAnalysis` | Portfolio-level risk metrics | 3-4 |
| `PortfolioOptimizationResult` | Optimized portfolio allocation | 4 |
| `MacroScenario` | Macro scenario modeling | 4 |
| `RebalancingRule` | Rebalancing constraints and rules | 3-4 |
| `MultiScenarioAnalysis` | Analysis across multiple scenarios | 4 |

**Data Flow:**
1. **Phase 3** - Portfolio construction from trading decisions
2. **Phase 4** - PortfolioOptimizationNode optimizes weights
3. Risk analysis computed across scenarios
4. Output feeds into production_models.py for backtesting

**Key Features:**
- Multi-scenario analysis (bull, bear, sideways markets)
- Risk constraints (max drawdown, VaR, correlation limits)
- Efficient frontier computation

---

### 5. **production_models.py** (11.4 KB)
**Purpose:** Phase 5 backtesting and real-time production deployment

**Classes:**
| Class | Purpose |
|-------|---------|
| `BacktestPeriod` | Definition of backtest time period |
| `BacktestResult` | Complete backtest performance metrics |
| `EfficientFrontierPoint` | Single point on efficient frontier |
| `EfficientFrontierData` | Complete frontier curve |
| `TransactionExecutionPlan` | Live trading execution plan |
| `PortfolioSnapshot` | Current portfolio state snapshot |
| `LiveTradingSession` | Active live trading session |
| `PerformanceMetricsSnapshot` | Real-time performance metrics |
| `TransactionCostAnalysis` | Transaction cost breakdown |
| `PerformanceAttribution` | Return attribution analysis |

**Data Flow:**
1. **Phase 5a** - BacktestingEngineNode runs historical backtest
2. **Phase 5a** - Computes EfficientFrontierData
3. **Phase 5b** - TransactionExecutionPlan created for live trading
4. **Phase 5b** - PortfolioSnapshot tracks current state
5. **Phase 5b** - Performance metrics updated every period

**Usage Example:**
```python
from src.models import BacktestResult, PerformanceMetricsSnapshot

backtest = BacktestResult(
    symbol="SPY",
    total_return=0.25,
    sharpe_ratio=1.5,
    max_drawdown=-0.12,
    win_rate=0.65
)

metrics = PerformanceMetricsSnapshot(
    total_return=0.15,
    daily_return=0.001,
    volatility=0.18,
    sharpe_ratio=1.8
)
```

---

### 6. **broker_models.py** (8.9 KB)
**Purpose:** Phase 6 broker API integration and order/execution tracking

**Classes:**
| Class | Purpose |
|-------|---------|
| `BrokerAccount` | Broker account credentials and metadata |
| `Order` | Pending or filled order |
| `BrokerPosition` | Current holdings in broker account |
| `Trade` | Completed trade with P&L |
| `BrokerAccountState` | Real-time account status |
| `BrokerExecutionPlan` | How to route orders to brokers |
| `ComplianceRecord` | Audit trail of trades |

**Data Flow:**
1. **Phase 6** - TransactionExecutionPlan converted to Orders
2. **Phase 6** - Orders routed via BrokerExecutionPlan
3. **Phase 6** - Order execution tracked and confirmed
4. **Phase 6** - Completed trades recorded in ComplianceRecord
5. **Phase 6** - BrokerAccountState updated

**Key Features:**
- Support for multiple brokers (Alpaca, Interactive Brokers)
- Order state transitions (pending → filled → settled)
- Compliance and audit trail

---

### 7. **advanced_models.py** (15.4 KB)
**Purpose:** Phase 7 advanced strategies and complex derivatives

**Classes:**
| Class | Purpose |
|-------|---------|
| `OptionContract` | Options contract specification and Greeks |
| `FuturesContract` | Futures contract specs and quotes |
| `CryptoDerivative` | Crypto perpetual and derivative specs |
| `MultiLegOrder` | Complex multi-leg order (spreads, straddles) |
| `GreeksSnapshot` | Portfolio-level Greeks for hedging |
| `HedgeAllocation` | Hedging recommendation and allocation |
| `StrategyPerformance` | Strategy P&L and metrics |
| `VolatilityProfile` | Volatility regime and term structure |
| `PairCorrelation` | Pair trading correlation analysis |

**Data Flow:**
1. **Phase 7** - AdvancedAnalysisNode identifies derivatives opportunities
2. **Phase 7** - StrategyBuilder constructs MultiLegOrder
3. **Phase 7** - GreeksSnapshot computed for risk monitoring
4. **Phase 7** - HedgeAllocation recommended
5. **Phase 7** - Execution routed through BrokerExecutionPlan

**Key Features:**
- Greeks calculation (delta, gamma, vega, theta, rho)
- Multi-leg order optimization
- Volatility regime identification

---

### 8. **deerflow_state.py** (11.7 KB)
**Purpose:** Master state object integrating all phases

**The DeerflowState Class:**
```python
class DeerflowState:
    """Master state object for the entire trading workflow."""
    
    # Phase 1-2: Data and initial analysis
    ticker_data: Optional[TickerData]
    technical_analysis: Optional[TechnicalAnalysis]
    fundamental_analysis: Optional[FundamentalAnalysis]
    news_analysis: Optional[NewsAnalysis]
    
    # Phase 2-3: Multi-analyst consensus
    growth_analysis: Optional[GrowthAnalysis]
    risk_analysis: Optional[RiskAnalysis]
    macro_analysis: Optional[MacroAnalysis]
    consensus_signal: Optional[ConsensusSignal]
    trading_decision: Optional[TradingDecision]
    
    # Phase 3-4: Portfolio level
    portfolio_risk: Optional[PortfolioRiskAnalysis]
    portfolio_optimization: Optional[PortfolioOptimizationResult]
    
    # Phase 5: Backtesting and production
    backtest_result: Optional[BacktestResult]
    efficient_frontier_data: Optional[EfficientFrontierData]
    transaction_execution_plan: Optional[TransactionExecutionPlan]
    
    # Phase 6: Broker integration
    broker_account_state: Optional[BrokerAccountState]
    orders: List[Order]
    positions: List[BrokerPosition]
    trades: List[Trade]
    
    # Phase 7: Advanced strategies
    option_positions: List[OptionContract]
    hedge_allocations: List[HedgeAllocation]
```

**Key Methods:**
- `get_analyst_results()` - Get all analyst outputs
- `has_complete_analysis()` - Check if all phases complete
- `add_error(node_id, error_msg)` - Log errors by node
- `update_timestamp()` - Update last modified time

**State Flow:**
1. Start with empty DeerflowState
2. Each phase populates its section
3. Later phases can reference earlier phases
4. Nodes check prerequisites before execution
5. Final state contains complete trading workflow result

---

## __init__.py - Public API

The `__init__.py` file re-exports all classes for backward compatibility:

```python
from .deerflow_state import DeerflowState
from .base import AnalystType, SignalType, DataProvider, MarketRegime
from .ticker_models import TickerData, TechnicalAnalysis, ...
from .analysis_models import GrowthAnalysis, RiskAnalysis, ...
# ... etc
```

**Import pattern (preferred):**
```python
# Direct from models package
from src.models import DeerflowState, TickerData, TradingDecision
```

---

## Phase-to-Model Mapping

| Phase | Duration | Primary Models | Output |
|-------|----------|-----------------|--------|
| **1** | Daily | TickerData | Raw market data |
| **2** | Daily | TechnicalAnalysis, FundamentalAnalysis, MacroAnalysis | Multiple analyst perspectives |
| **3** | Daily | ConsensusSignal, TradingDecision | Trading recommendation |
| **4** | Weekly | PortfolioOptimizationResult, PortfolioRiskAnalysis | Optimized portfolio |
| **5** | Monthly | BacktestResult, TransactionExecutionPlan | Live trading plan |
| **6** | Real-time | Order, BrokerAccountState, Trade | Executed trades |
| **7** | As-needed | OptionContract, HedgeAllocation, StrategyPerformance | Derivative strategies |

---

## Common Patterns

### Creating a Complete Analysis Flow
```python
from src.models import (
    DeerflowState, TickerData, TechnicalAnalysis, 
    ConsensusSignal, TradingDecision, GrowthAnalysis
)

state = DeerflowState()
state.ticker_data = TickerData(...)  # Phase 1
state.technical_analysis = TechnicalAnalysis(...)  # Phase 2
state.growth_analysis = GrowthAnalysis(...)  # Phase 2
state.consensus_signal = ConsensusSignal(...)  # Phase 3
state.trading_decision = TradingDecision(...)  # Phase 3
```

### Validating Data at Each Phase
```python
def validate_phase3(state: DeerflowState) -> bool:
    """Check if Phase 3 prerequisites met."""
    return (
        state.consensus_signal is not None and
        state.trading_decision is not None and
        state.trading_decision.action != "HOLD"
    )
```

### Error Handling with Analyst Types
```python
for result in state.get_analyst_results():
    if result.analyst_type == AnalystType.MACRO:
        # Handle macro-specific logic
        pass
```

---

## Best Practices

1. **Use Type Hints** - Always use DeerflowState in function signatures
   ```python
   def process_data(state: DeerflowState) -> DeerflowState:
   ```

2. **Check Prerequisites** - Verify required models exist before accessing
   ```python
   if state.consensus_signal is None:
       raise ValueError("ConsensusSignal required")
   ```

3. **Use Enums** - Use AnalystType, SignalType enums instead of strings
   ```python
   if result.signal == SignalType.BUY:  # Good
   if result.signal == "buy":  # Avoid
   ```

4. **Immutability** - Keep models immutable when possible (Pydantic BaseModel)

5. **Clear Ownership** - Each phase owns its models; don't bypass phases

---

## Backward Compatibility

The old `state.py` monolithic file has been refactored into these modules. All imports are re-exported in `__init__.py`, so existing code continues to work:

```python
# Old way (still works)
from src.models import DeerflowState

# New way (also works)
from src.models.deerflow_state import DeerflowState
```

---

## Testing

Each module is covered by test cases in `tests/test_state.py`:
- ✅ Enum validation (base.py)
- ✅ Model creation and validation (all phase modules)
- ✅ State schema completeness (deerflow_state.py)
- ✅ Cross-phase dependencies

To run tests:
```bash
pytest tests/test_state.py -v
```

Expected: **22/22 PASSED** ✅

---

## Future Extensions

- **Phase 8+** - Add new phase modules following the same pattern
- **Model Versioning** - Track schema versions for compatibility
- **Serialization** - Export/import state to/from JSON for persistence
- **Observability** - Add instrumentation for state transitions
