# Phase 7: Advanced Strategies & Derivatives Trading

**Status**: 🚀 Planned  
**Target Lines**: ~3,200 lines (nodes + state models + derivatives engines)  
**Timeline**: Post-Phase 6  

---

## Executive Summary

Phase 7 expands trading capabilities beyond equities into advanced strategies including options, futures, crypto derivatives, and sophisticated hedging techniques. The system evolves from single-leg equity trades to multi-leg strategies, volatility arbitrage, and directional/non-directional hedging.

### Phase 7 Objectives

1. **Options Trading** - Calls, puts, spreads, straddles, collars, butterflies
2. **Futures Trading** - Index futures, commodity futures, ES/NQ/YM contracts
3. **Crypto Derivatives** - Perpetual futures, options on spot
4. **Hedging Strategies** - Long/short pairs, sector hedges, tail risk protection
5. **Strategy Chaining** - Multi-leg execution with coordinated timing
6. **Greeks Management** - Delta, gamma, theta, vega, rho monitoring
7. **Volatility Arbitrage** - Implied vs realized vol strategies

---

## Architecture Overview

### Component Hierarchy

```
              Advanced Strategy Engine
                        |
          +-----+-------+-------+-----+
          |     |       |       |     |
      Options  Futures Crypto  Pairs Combo
      Engine   Engine   Engine  Engine Strategy
        |       |        |       |     Optimizer
        |       |        |       |
    Greeks   Contract  Derivatives Correlation
    Monitor  Monitor   Monitor    Engine
        |       |        |        |
      Greeks  Curve    Funding   Dynamic
      Hedge   Manager   Manager  Rebalancer
```

### Data Flow

```
Phase 6 Execution (Equities)
  |
  v
Identify Hedging Need OR Speculative Opportunity
  |
  v
Analyze Available Strategies (Options/Futures/Hybrids)
  |
  v
Calculate Greeks & Risk Metrics
  |
  v
Validate Against Account Limits
  |
  v
Execute Multi-Leg Strategy
  |
  v
Monitor Greeks & Rebalance
  |
  v
Close Strategy When Thesis Complete
```

---

## New State Models

### 1. OptionContract
**Purpose**: Details for equity/index options contracts.

```python
class OptionContract(BaseModel):
    contract_id: str              # Unique contract ID
    ticker: str                   # Underlying symbol
    contract_type: str            # CALL or PUT
    expiration: date              # Expiration date
    strike: float                 # Strike price
    bid: float                    # Current bid price
    ask: float                    # Current ask price
    last: float                   # Last trade price
    volume: int                   # Daily volume
    open_interest: int            # Total open contracts
    implied_volatility: float     # IV as decimal (0.25 = 25%)
    delta: float                  # Delta (0 to 1 for calls, -1 to 0 for puts)
    gamma: float                  # Gamma (curvature)
    theta: float                  # Theta (daily decay)
    vega: float                   # Vega (IV sensitivity)
    rho: float                    # Rho (interest rate sensitivity)
    last_updated: datetime        # Quote timestamp
    is_tradeable: bool            # Is option currently tradeable
```

### 2. FuturesContract
**Purpose**: Futures contract specifications and quotes.

```python
class FuturesContract(BaseModel):
    contract_id: str              # Unique contract ID
    symbol: str                   # Futures symbol (ES, NQ, YM, GC, CL, etc)
    contract_code: str            # Full code (ESH24 = Mar 2024 E-mini S&P)
    expiration: date              # Last trading day
    multiplier: float             # Contract size ($50 for ES, $100 for NQ)
    bid: float                    # Current bid
    ask: float                    # Current ask
    current_price: float          # Mid-market
    daily_change: float           # Change today
    daily_change_pct: float       # % change today
    volume: int                   # Daily volume
    open_interest: int            # Total open contracts
    settlement_price: float       # Previous day settlement
    bid_volume: int               # Bid size
    ask_volume: int               # Ask size
    last_updated: datetime        # Quote timestamp
    contract_type: str            # INDEX, COMMODITY, FOREX, CRYPTO
    exchange: str                 # CME, ICE, etc
```

### 3. CryptoDerivative
**Purpose**: Cryptocurrency futures and perpetuals.

```python
class CryptoDerivative(BaseModel):
    contract_id: str              # Unique ID
    underlying: str               # BTC, ETH, SOL, etc
    contract_type: str            # PERPETUAL or FUTURES
    expiration: Optional[date]    # Null for perpetuals
    bid: float                    # Current bid
    ask: float                    # Current ask
    index_price: float            # Underlying spot price
    mark_price: float             # Mark price (perps have funding)
    funding_rate: float           # Hourly funding rate (perps)
    funding_rate_8h: float        # Predicted 8-hour rate
    bid_volume: float             # In contract amount
    ask_volume: float             # In contract amount
    volume_24h: float             # Volume in USD
    liquidation_price_long: float # Long liquidation level
    liquidation_price_short: float # Short liquidation level
    open_interest: float          # Total open contracts
    last_updated: datetime        # Quote timestamp
    exchange: str                 # Binance, FTX, Bybit, Deribit, etc
```

### 4. MultiLegOrder
**Purpose**: Coordinated multi-leg strategy execution.

```python
class MultiLegOrder(BaseModel):
    strategy_id: str              # Unique strategy ID
    strategy_name: str            # CALL_SPREAD, IRON_CONDOR, PAIR_TRADE, etc
    legs: List[Dict]              # Each leg with order details
    # Each leg contains:
    #   - ticker/contract_id
    #   - action (BUY/SELL)
    #   - quantity
    #   - type (option/stock/future)
    #   - price (limit/market)
    #   - filled_qty
    #   - filled_price
    total_cost: float             # Net debit/credit for entire strategy
    max_loss: float               # Max loss if all legs filled at limit
    max_profit: float             # Max profit on the strategy
    breakeven: float              # Breakeven price(s) - can be multiple
    created_at: datetime          # Creation time
    executed_at: Optional[datetime]  # Full execution time
    status: str                   # PLANNED, EXECUTING, FILLED, PARTIAL, CANCELLED
    execution_order: List[int]    # Order to execute legs (order IDs)
    notes: str                    # Strategy thesis and exit plan
```

### 5. GreeksSnapshot
**Purpose**: Real-time Greeks for position monitoring.

```python
class GreeksSnapshot(BaseModel):
    snapshot_id: str              # Unique snapshot ID
    timestamp: datetime           # As of time
    position_id: str              # Which position/strategy
    
    # Aggregate Greeks for position
    total_delta: float            # Share equivalents
    total_gamma: float            # Delta change per 1% move
    total_theta: float            # Daily decay in USD
    total_vega: float             # Per 1% IV change
    total_rho: float              # Per 1% rate change
    
    # Greeks by leg (if multi-leg)
    leg_greeks: List[Dict]        # Delta, gamma, theta, vega for each
    
    # Risk metrics
    delta_pct: float              # % of portfolio at risk
    theta_as_return_pct: float    # Theta decay as % of position value
    vega_exposure: float          # IV sensitivity in dollars
    gamma_exposure: float         # Convexity in dollars
    
    # Alerts
    delta_drift_alert: bool       # Delta drifted >10% from target
    theta_decay_strong: bool      # High time decay (positive theta)
    gamma_risk_high: bool         # High gamma risk near expiration
    vega_exposure_alert: bool     # High IV sensitivity
    
    rebalance_needed: bool        # Should rebalance for delta neutral
    rebalance_shares: Optional[int]  # How many shares to hedge/unhedge
    rebalance_cost: Optional[float]  # Cost of rebalance
```

### 6. HedgeAllocation
**Purpose**: Recommended hedging position sizing.

```python
class HedgeAllocation(BaseModel):
    allocation_id: str            # Unique allocation ID
    base_position: Dict           # Original position being hedged
    # {ticker, quantity, entry_price, current_price}
    
    hedging_strategies: List[Dict]  # Ranked by efficiency
    # Each strategy:
    # - strategy_name (PUT_PROTECTION, COLLAR, SHORT_SALE, CALL_SPREAD)
    # - cost (net debit/credit)
    # - max_loss (capped downside)
    # - max_gain (limited upside)
    # - breakeven_price
    # - time_to_expiration (if options)
    # - Greeks at expiration
    
    optimal_hedge: str            # Recommended strategy
    hedge_ratio: float            # % of position to hedge
    cost_as_pct_position: float   # Hedge cost as % of position value
    protection_level: float       # Downside protected to this price
    
    thesis: str                   # Why this hedge
    conditions_to_close: List[str]  # When to close hedge
    max_duration_days: int        # How long to hold
    
    created_at: datetime
    expires_at: datetime          # When this recommendation expires
```

### 7. StrategyPerformance
**Purpose**: Track performance of multi-leg strategies.

```python
class StrategyPerformance(BaseModel):
    performance_id: str           # Unique ID
    strategy_id: str              # Which strategy
    strategy_name: str
    
    # Entry details
    entry_price: float            # Mark price when entered
    entry_date: datetime
    entry_capital: float          # Capital deployed
    
    # Current status
    current_price: float          # Current mark
    days_held: int
    
    # P&L
    theoretical_pnl: float        # If closed at current prices
    theta_accumulated: float      # Time decay captured
    gamma_pnl: float              # Realized gamma P&L
    vega_pnl: float               # IV change P&L
    delta_pnl: float              # Directional P&L
    
    # Return metrics
    return_pct: float             # % return on capital
    annualized_return: float      # Annualized %
    sharpe_ratio: Optional[float]   # Risk-adjusted return
    max_drawdown: float           # Worst case P&L
    
    # Greeks current
    current_delta: float
    current_theta: float
    current_vega: float
    
    # Exit strategy
    target_profit: float          # Close when P&L reaches this
    stop_loss: float              # Close if P&L drops to this
    time_exit: Optional[datetime]   # Close by this date
    exit_reason: str              # Why was it closed
    
    status: str                   # ACTIVE, CLOSED, EXPIRED
    closed_at: Optional[datetime]
    final_pnl: Optional[float]    # Actual P&L when closed
```

### 8. VolatilityProfile
**Purpose**: Volatility regime and arbitrage tracking.

```python
class VolatilityProfile(BaseModel):
    profile_id: str               # Unique ID
    timestamp: datetime           # As of time
    ticker: str                   # Which security
    
    # Implied volatility
    iv_30d: float                 # 30-day IV
    iv_60d: float                 # 60-day IV
    iv_90d: float                 # 90-day IV
    iv_term_structure: str        # UPWARD_SLOPING, FLAT, INVERTED
    
    # Realized volatility
    realized_vol_20d: float       # Last 20 days realized
    realized_vol_60d: float       # Last 60 days realized
    
    # Skew and surface
    put_call_skew: float          # OTM put IV vs OTM call IV
    volatility_smile: Dict        # IV by strike
    
    # Historical context
    iv_percentile: float          # 0-100 where current IV ranks historically
    iv_high_52w: float            # 52-week high
    iv_low_52w: float             # 52-week low
    
    # Arbitrage opportunities
    iv_vs_rv_spread: float        # (IV - RV) in basis points
    calendar_spread_available: bool  # Different expirations have arbitrage
    butterfly_available: bool     # Butterfly spread arbitrage
    skew_arbitrage: float         # Skew spread value
    
    # Forecast
    vol_forecast_7d: float        # 1-week predicted vol
    vol_forecast_30d: float       # 1-month predicted vol
    vol_direction_bias: str       # UP, DOWN, STABLE based on curve
    
    recommendation: str           # VIX is high/normal/low, suggest strategy
```

### 9. PairCorrelation
**Purpose**: Track correlations for pair trading strategies.

```python
class PairCorrelation(BaseModel):
    pair_id: str                  # Unique pair ID
    ticker1: str                  # First security
    ticker2: str                  # Second security
    correlation_period_days: int  # Calculated over how long
    
    # Correlation metrics
    correlation_60d: float        # -1 to 1
    correlation_252d: float       # Long-term
    covariance_60d: float
    beta_1_vs_2: float            # Ticker1 beta vs Ticker2
    
    # Spread analysis
    current_spread: float         # Ticker1 - Ticker2 price/ratio
    mean_spread: float            # Historical mean
    std_spread: float             # Standard deviation
    zscore_spread: float          # How many stds from mean
    
    # Mean reversion metrics
    halflife_days: int            # How long to mean revert
    mean_revert_probability: float # % likely to revert
    
    # Strategy recommendation
    current_trade: str            # LONG_1_SHORT_2, LONG_2_SHORT_1, NONE
    entry_zscore: float           # Zscore when entered
    exit_zscore: float            # Target exit zscore
    
    # Execution
    shares_1: int                 # Quantity to buy/sell of ticker1
    shares_2: int                 # Quantity to buy/sell of ticker2
    hedge_ratio: float            # Qty2/Qty1 to achieve beta neutrality
    
    status: str                   # MONITORING, ACTIVE_TRADE, CLOSED
    entry_date: Optional[datetime]
    exit_date: Optional[datetime]
    pnl: Optional[float]          # If closed
    
    next_review: datetime         # When to reassess pair
```

### 10. State Extension for Phase 7

```python
# Add to DeerflowState:

# Derivatives tracking
active_options: Dict[str, OptionPosition] = Field(default_factory=dict)
active_futures: Dict[str, FuturesPosition] = Field(default_factory=dict)
active_crypto_derivatives: Dict[str, CryptoPosition] = Field(default_factory=dict)

# Strategies
active_strategies: Dict[str, MultiLegOrder] = Field(default_factory=dict)
strategy_performance: Dict[str, StrategyPerformance] = Field(default_factory=dict)

# Greeks and risk
current_greeks: Dict[str, GreeksSnapshot] = Field(default_factory=dict)
greek_alerts: List[Dict] = Field(default_factory=list)

# Hedging
recommended_hedges: Dict[str, HedgeAllocation] = Field(default_factory=dict)
active_hedges: Dict[str, MultiLegOrder] = Field(default_factory=dict)

# Volatility
volatility_profiles: Dict[str, VolatilityProfile] = Field(default_factory=dict)
vol_opportunities: List[Dict] = Field(default_factory=list)

# Pair trading
correlations: Dict[str, PairCorrelation] = Field(default_factory=dict)
active_pairs: Dict[str, PairCorrelation] = Field(default_factory=dict)

# Greeks management
target_delta: float = Field(0.0)  # Portfolio-level delta target
rebalance_threshold: float = Field(0.15)  # Rebalance if delta drifts >15%
last_greek_rebalance: Optional[datetime] = None
```

---

## New Nodes (10 total)

### 1. OptionsAnalysisNode
**Purpose**: Fetch and analyze options chains.

**Input**: Tickers from strategy decision  
**Output**: `analyzed_options`, Greeks for strategies

```python
Responsibilities:
- Fetch options chains from data provider
- Parse strike selection for strategies
- Calculate Greeks (delta, gamma, theta, vega, rho)
- Identify deep ITM/OTM contracts
- Filter liquid contracts
- Generate strategy recommendations
- Estimate strategy probabilities
```

### 2. FuturesAnalysisNode
**Purpose**: Analyze futures contracts for strategies.

**Input**: Asset allocation, hedging needs  
**Output**: `viable_futures`, contract recommendations

```python
Responsibilities:
- Identify relevant futures (ES for broad, sector ETF futures)
- Fetch contract specifications and quotes
- Calculate contract multipliers and notional exposure
- Compare liquidity across expirations
- Identify arbitrage opportunities (spot-vs-futures)
- Recommend contracts for hedging/speculation
```

### 3. CryptoDerivativesNode
**Purpose**: Analyze crypto perpetuals and futures options.

**Input**: Crypto holdings, hedging needs  
**Output**: `crypto_hedging_strategies`, perpetual recommendations

```python
Responsibilities:
- Fetch perpetual futures from multiple exchanges
- Get funding rates and mark prices
- Calculate liquidation levels
- Identify funding rate arbitrage
- Analyze cross-exchange spreads
- Recommend hedges or speculative positions
```

### 4. StrategyBuilderNode
**Purpose**: Construct multi-leg strategies.

**Input**: Market view, capital, Greeks targets  
**Output**: `constructed_strategies`, multi-leg orders

```python
Responsibilities:
- Match market views to strategies (bullish → call spread, etc)
- Calculate Greeks for strategy combinations
- Optimize strike selection for cost/risk
- Generate multi-leg execution plans
- Calculate max profit/loss/breakeven
- Estimate probability of profit
- Validate against account limits
```

### 5. GreeksMonitorNode
**Purpose**: Real-time Greeks tracking and rebalancing alerts.

**Input**: Active options positions, current prices  
**Output**: `greek_snapshots`, rebalance recommendations

```python
Responsibilities:
- Fetch current option prices
- Recalculate Greeks for all positions
- Aggregate portfolio delta/gamma/theta
- Compare to targets (delta neutral, etc)
- Generate rebalancing recommendations
- Track theta decay accumulation
- Flag high gamma risk near expiration
- Alert on vega exposure to IV changes
```

### 6. DeltaHedgingNode
**Purpose**: Maintain delta-neutral portfolios.

**Input**: Current Greeks, target delta  
**Output**: Hedging orders to maintain neutrality

```python
Responsibilities:
- Calculate delta drift from target
- Determine shares to buy/sell for hedge
- Generate spot stock orders
- Generate option hedge orders (longer duration)
- Optimize hedge cost
- Schedule rebalancing frequency
- Track hedge effectiveness
```

### 7. HedgeRecommenderNode
**Purpose**: Suggest optimal hedging strategies.

**Input**: Long positions, risk tolerance, capital available  
**Output**: `recommended_hedges` ranked by efficiency

```python
Responsibilities:
- Analyze downside risk of position
- Generate put protection scenarios
- Generate collar structures
- Generate short-sale hedges
- Generate call-spread hedges
- Calculate cost/benefit of each
- Estimate protection levels
- Provide exit strategies for hedges
```

### 8. VolatilityArbitrageNode
**Purpose**: Identify and recommend vol arbitrage trades.

**Input**: Volatility profiles, calendar spreads  
**Output**: Vol arbitrage trade recommendations

```python
Responsibilities:
- Analyze implied vs realized volatility
- Identify skew arbitrage (put/call skew)
- Detect calendar spread opportunities
- Calculate butterfly spread values
- Compare IV term structure
- Rank by risk-reward
- Generate option spread orders
- Monitor for mean reversion
```

### 9. PairTradingNode
**Purpose**: Identify and monitor pairs for mean reversion.

**Input**: Correlation matrix, price data  
**Output**: Active pairs, execution signals

```python
Responsibilities:
- Calculate rolling correlations
- Detect correlation breakdown
- Identify mean reversion opportunities
- Calculate hedge ratios
- Monitor for regression to mean
- Generate entry/exit signals
- Track pair P&L
- Manage correlated risk
```

### 10. StrategyExecutorNode
**Purpose**: Execute multi-leg strategy orders.

**Input**: Multi-leg strategy orders from builder  
**Output**: Executed orders, partial fills management

```python
Responsibilities:
- Validate multi-leg orders
- Determine execution sequence
- Submit legs in optimal order
- Handle partial fills
- Manage legs across brokers
- Cancel unmatched legs if needed
- Generate execution reports
- Track strategy entry price
```

---

## Graph Topology (Phases 1-7)

```
                  [Phase 1-6: Core System]
                    [Equities & Futures]
                           |
        [Identify Hedging OR Speculative Opportunity]
                           |
                +-----------+----------+
                |           |          |
        [OptionsAnalysis]  [Futures]  [Crypto]
                |           |          |
        [StrategyBuilder]---+----------+
                |
        +-----------+---------+----------+
        |           |         |          |
    [Greeks        [Delta     [Hedge    [Vol
     Monitor]    Hedging]   Recommender] Arbitrage]
        |           |         |          |
        +-----------+---------+----------+
                |
       [PairTrading] (parallel analysis)
                |
        [StrategyExecutor]
                |
        +-----------+----------+
        |           |          |
    [Options    [Futures    [Crypto]
    Execution]  Execution]
        |           |        |
        +-------+---+--------+
                |
        [GreeksMonitor] (continuous)
                |
            Monitor ──→ Rebalance
```

---

## Implementation Plan

### Step 1: State Models (500 lines)
- Options, futures, crypto derivative models
- Multi-leg orders and strategy execution
- Greeks monitoring and hedging structures
- Volatility profiles and pair correlations

### Step 2: Strategy Definitions (600 lines)
- Predefined strategy templates (spreads, straddles, etc)
- Greeks calculators for each strategy type
- Probability of profit calculations
- Risk/reward optimization
- Strike selection algorithms

### Step 3: Nodes (1,600 lines)
- Options/futures/crypto analysis (450)
- Strategy builder with Greeks calc (300)
- Greeks monitoring and alerts (300)
- Delta hedging automation (250)
- Hedge recommendations (200)
- Vol arbitrage detection (100)
- Pair trading correlation (100)
- Multi-leg execution (300)

### Step 4: Greeks Engines (400 lines)
- Black-Scholes calculation
- Greeks sensitivities
- Implied volatility solutions
- Options Greeks aggregation
- Portfolio delta tracking
- Gamma risk measurement
- Theta decay visualization

### Step 5: Graph Integration (300 lines)
- Connect Phase 7 with Phase 1-6
- Create derivatives trading pipeline
- Hedging decision logic
- Multi-strategy coordination
- Rebalancing triggers

### Step 6: Tests (800 lines)
- Unit tests for Greeks calculations
- Strategy builder tests
- Hedging recommendation tests
- Pair trading correlation tests
- Multi-leg execution flow tests
- Greeks monitoring tests
- Rebalancing logic tests

### Step 7: Documentation (400 lines)
- Phase 7 completion report
- Options/futures trading guides
- Greeks management best practices
- Hedging strategy runbooks
- Volatility arbitrage examples

---

## Key Features

### 1. Options Trading
- **Single Leg**: Long calls, long puts, short calls, short puts
- **Vertical Spreads**: Bull call, bear call, bull put, bear put
- **Straddles/Strangles**: Long straddle, short strangle
- **Iron Condor**: Four-leg income strategy
- **Collar**: Long stock + long put + short call
- **Butterfly**: Limited risk, limited profit

### 2. Futures Trading
- **Index Futures**: ES (S&P 500), NQ (Nasdaq), YM (Dow)
- **Commodity Futures**: GC (gold), CL (crude), NG (natural gas)
- **Micro Contracts**: MES, MNQ, MYM for smaller accounts
- **Spread Contracts**: Calendar spreads, inter-month
- **Calendar Arbitrage**: Spot-vs-futures exploitation

### 3. Crypto Derivatives
- **Perpetual Futures**: Binance, FTX, Bybit, Deribit
- **Quarterly Futures**: Traditional expiration contracts
- **Options**: Deribit options on BTC/ETH
- **Funding Rate Trading**: Capture periodic funding payments
- **Cross-Exchange Arbitrage**: Binance vs FTX basis trades

### 4. Greeks Management
- **Delta**: Directional exposure, neutrality targets
- **Gamma**: Curvature, rebalancing needs, convexity trades
- **Theta**: Time decay, income strategies
- **Vega**: IV sensitivity, vol trades, exposure to vol changes
- **Rho**: Interest rate sensitivity (long duration)

### 5. Hedging Strategies
- **Protective Puts**: Downside protection on long stock
- **Collars**: Protection + cost reduction via covered calls
- **Spreads**: Reduce cost via offsetting long/short legs
- **Short Hedges**: Short stock or short futures as hedge
- **Volatility Hedges**: Long vol positions for tail risk

### 6. Volatility Arbitrage
- **Cal Spread**: Buy near-term, sell long-term (or vice versa)
- **Put/Call Skew**: Exploit asymmetric IV
- **Butterfly Spreads**: Capture volatility smile
- **Ratio Spreads**: Vega trades
- **Straddle Buying**: Long vol at low vol levels

### 7. Pair Trading
- **Mean Reversion**: Trade correlation breakdowns
- **Beta Neutral**: Hedge out market exposure
- **Sector Neutral**: Hedge sector exposure
- **Mean Reversion Signals**: Entry on N-sigma moves
- **Exit Strategies**: Revert to mean or time-based

---

## Testing Strategy

### Unit Tests (200 tests)
- Black-Scholes Greeks calculations (+/- 0.001)
- Multi-leg order validation
- Strategy builder logic
- Delta hedge rebalancing algorithms
- Pair correlation calculations
- IV surface interpolation

### Integration Tests (80 tests)
- Full options chain analysis workflow
- Futures contract analysis and liquidity
- Multi-leg strategy construction
- Greeks aggregation for portfolio
- Delta hedging effectiveness
- Volatility arbitrage detection
- Pair trading mean reversion

### End-to-End Tests (30 tests)
- Build and execute call spread
- Build and execute iron condor
- Build and execute collar (protection)
- Delta hedge stock position with options
- Execute pair trade and monitor
- Rebalance Greeks daily
- Close strategies at profit target

### Backtests (20 tests)
- Historical options strategies (2020-2024)
- Vol arbitrage seasonality
- Delta hedging P&L vs rehedge frequency
- Pair trading mean reversion rates
- Collar payoff diagrams vs spot moves

---

## Success Criteria

### Functional
- ✅ Calculate Greeks accurately (<0.1% error vs market)
- ✅ Execute multi-leg options strategies without errors
- ✅ Maintain delta-neutral portfolio within 5% tolerance
- ✅ Identify and execute vol arbitrage trades
- ✅ Detect and trade mean-reverting pairs
- ✅ Manage Greeks rebalancing automatically

### Performance
- < 100ms options chain analysis
- < 500ms multi-leg strategy construction
- < 200ms Greeks recalculation
- < 1 second delta hedge rebalance decision
- < 2 seconds pair correlation update

### Reliability
- Identify 80%+ of profitable vol arbitrage setups
- Mean-reverting pairs: 70%+ accuracy
- Hedge effectiveness: 90%+ of target
- Greeks monitoring: 99.9% uptime

### Risk
- Options losses capped by strategy design
- Options spread max loss validated before execution
- Greeks alerts trigger before drift becomes costly
- Hedges rebalance before delta drifts >10%

---

## Example Strategies

### Strategy 1: Bull Call Spread
**Setup**: Buy OTM call, sell higher strike call  
**Cost**: Net debit (lower than single call)  
**Max Loss**: Debit paid  
**Max Profit**: Difference in strikes - debit  
**Best For**: Moderate bullish view with defined risk

### Strategy 2: Iron Condor
**Setup**: Sell OTM put spread + sell OTM call spread  
**Cost**: Net credit (income)  
**Max Loss**: Strike width - credit  
**Max Profit**: Credit collected  
**Best For**: Income generation in stable markets

### Strategy 3: Protective Collar
**Setup**: Long stock + long put + short call  
**Cost**: Net debit (put cost - call premium)  
**Downside**: Protected to put strike  
**Upside**: Capped at call strike  
**Best For**: Protect profits while continuing upside

### Strategy 4: Delta-Hedged Long Call
**Setup**: Long call + short delta equivalent shares  
**Greeks**: Near-zero delta (vega and gamma positive)  
**P&L**: Volatility profits when realized > implied  
**Best For**: Volatility trades, income from theta

### Strategy 5: Pair Trade (Beta Neutral)
**Setup**: Long underperformer + short outperformer  
**Hedge**: Size legs so market beta = 0  
**P&L**: Correlation reversion profits, market neutral  
**Best For**: 130/30 strategy without market beta

### Strategy 6: Calendar Spread
**Setup**: Sell near-term volatility, buy longer-term  
**Theta**: Positive (near term decays faster)  
**Vega**: Positive (long vol > short vol)  
**Best For**: Capture positive theta + vol expansion

---

## Greeks Rebalancing Example

```
Current Portfolio:
- 100 shares AAPL @ $150 = $15,000 notional
- Current delta = +100 (fully directional)

Greeks Goals:
- Target delta = 0 (delta neutral)
- Acceptable range = -10 to +10

Options Available:
- AAPL 150 Call: Delta = +0.50, Cost = $2.50
- AAPL 150 Put: Delta = -0.50, Cost = $2.50

Hedging Decision:
- Need to reduce delta by 100
- Buy 200 puts (200 × -0.50 = -100 delta)
- Cost: 200 × $2.50 = $500 (0.33% of portfolio)
- New delta: (100) + (-100) = 0 ✓

Ongoing Monitoring:
- Daily: Recalculate delta, check for 10-delta drift
- If drifts: Sell shares or calls to rebalance
- If put expires: Roll to next month
```

---

## Deployment Checklist

- [ ] Validate Black-Scholes Greeks accuracy
- [ ] Set up options data feeds (chains, quotes)
- [ ] Set up futures data feeds
- [ ] Set up crypto derivatives feeds (Deribit, Binance)
- [ ] Configure multi-leg order execution
- [ ] Backtest strategies on historical data
- [ ] Paper trade options for 4 weeks
- [ ] Execute small real trades (1 contract)
- [ ] Monitor Greeks daily
- [ ] Implement rebalancing automation
- [ ] Enable alerts for Greeks drift
- [ ] Document all strategies
- [ ] Create runbook for options trading

---

## Risk Management Rules

1. **Position Sizing**: Keep single strategy risk ≤ 2% of portfolio
2. **Greeks Limits**: 
   - Portfolio delta: -5 to +5 (delta neutral target)
   - Gamma: Total absolute gamma ≤ portfolio size
   - Theta: Daily decay < 1% of portfolio
   - Vega: IV move impact ≤ 2% of portfolio
3. **Expiration**: Close positions before last week of expiration
4. **Assignment**: Handle assignment of short options
5. **Liquidity**: Only use contracts with bid-ask < $0.05 difference
6. **Correlations**: Monitor pair correlation breakdowns weekly

---

## Phase 7 Milestones

| Week | Milestone | Target |
|------|-----------|--------|
| 1-2 | Options analysis node + Greeks engine | Calculate Greeks accurately |
| 3-4 | Strategy builder + multi-leg execution | Build & execute spreads |
| 5-6 | Greeks monitoring + delta hedging | Maintain delta neutral |
| 7-8 | Futures + crypto derivatives support | Hedge with non-equity assets |
| 9-10 | Vol arbitrage + pair trading | Execute multi-leg strategies |
| 11-12 | Testing + documentation + release | Phase 7 complete |

---

## Next Phases (Future)

### Phase 8: Machine Learning Integration
- ML-based volatility forecasting
- Trade timing predictions
- Greeks optimal rebalancing
- Strategy selection based on regime
- Options chain pattern recognition
- Funding rate forecasting for crypto

### Phase 9: Global Markets
- International equities options
- FX options and forwards
- Multi-currency hedging
- Cross-market arbitrage
- Global volatility surfaces

### Phase 10: Portfolio Optimization (Advanced)
- Full portfolio Greeks management
- Efficient frontier with derivatives
- CVaR (Conditional Value at Risk)
- Scenario analysis with strategies
- Stress testing across scenarios

---

## Conclusion

Phase 7 transforms the trading system into a sophisticated derivatives platform capable of leveraging options, futures, and crypto derivatives for hedging and speculation. With comprehensive Greeks management, volatility arbitrage, and pair trading capabilities, the system becomes a truly advanced quant platform capable of executing institutional-grade strategies across multiple asset classes.
