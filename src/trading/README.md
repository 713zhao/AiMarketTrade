# Trading Simulation System

The Trading Simulation System enables users to test trading strategies with virtual money based on AnalysisEngine recommendations. This allows validation of analysis algorithms without risking real capital.

## Architecture

### Components

1. **TradingSimulator**: Core component managing virtual portfolios and trade execution
2. **TradeExecutor**: Processes buy/sell orders with validation
3. **PerformanceCalculator**: Computes P&L and performance metrics
4. **BacktestEngine**: Replays historical recommendations for past performance analysis
5. **TradingIntegration**: Connects trading simulator with AnalysisEngine

### Data Models

- **Portfolio**: Virtual cash balance and stock positions
- **Position**: Stock holding with quantity and average cost basis
- **Trade**: Buy/sell transaction record
- **TradeHistory**: Persistent storage of all trades
- **PerformanceReport**: Comprehensive performance metrics
- **BacktestResult**: Results from historical backtesting

## Features

### Portfolio Management
- Create portfolios with initial cash balance
- Deposit additional virtual money
- Track cash and positions
- Save/load portfolio state

### Trade Execution
- Manual buy/sell orders
- Automatic execution based on recommendations
- Position sizing strategies (fixed amount or percentage)
- Confidence threshold filtering
- Complete trade validation

### Performance Tracking
- Realized and unrealized P&L
- Total return percentage
- Win rate and average profit/loss
- Maximum drawdown
- Comprehensive performance reports

### Backtesting
- Test strategies on historical data
- Chronological recommendation replay
- Isolated backtest portfolios
- Performance analysis

## Configuration

Add trading configuration to `config/default.yaml`:

```yaml
trading:
  # Initial cash balance for new portfolios
  initial_cash_balance: 100000.00
  
  # Minimum confidence score (0.0-1.0) to execute trades
  confidence_threshold: 0.70
  
  # Position sizing: "fixed_amount" or "percentage"
  position_sizing_strategy: "percentage"
  
  # Position size value
  # For "percentage": 0.10 = 10% of portfolio per trade
  # For "fixed_amount": dollar amount per trade
  position_size_value: 0.10
```

## Usage

### Programmatic Usage

```python
from decimal import Decimal
from stock_market_analysis.trading import TradingSimulator
from stock_market_analysis.components import ConfigurationManager

# Initialize
config_manager = ConfigurationManager()
simulator = TradingSimulator(config_manager)

# Create portfolio
portfolio_id = simulator.create_portfolio(Decimal("100000.00"))

# Execute manual trade
trade = simulator.execute_trade(
    portfolio_id=portfolio_id,
    symbol="AAPL",
    action="BUY",
    quantity=10,
    price=Decimal("150.00")
)

# Process recommendation
from stock_market_analysis.models import StockRecommendation, RecommendationType
recommendation = StockRecommendation(...)
trade = simulator.process_recommendation(portfolio_id, recommendation)

# Get performance report
report = simulator.get_performance_report(portfolio_id)
print(report.to_text())

# Save portfolio
simulator.save_portfolio(portfolio_id, "data/my_portfolio.json")

# Load portfolio
loaded_id = simulator.load_portfolio("data/my_portfolio.json")
```

### CLI Usage

```bash
# Create portfolio
python -m stock_market_analysis.trading.cli create-portfolio 100000 --save data/portfolio.json

# Deposit cash
python -m stock_market_analysis.trading.cli deposit data/portfolio.json 10000

# Execute trade
python -m stock_market_analysis.trading.cli trade data/portfolio.json BUY AAPL 10 150.00

# View portfolio
python -m stock_market_analysis.trading.cli view-portfolio data/portfolio.json

# View performance
python -m stock_market_analysis.trading.cli view-performance data/portfolio.json --format text
```

### Backtesting

```python
from stock_market_analysis.trading import BacktestEngine

# Initialize
engine = BacktestEngine(config_manager)

# Run backtest with historical recommendations
result = engine.run_backtest(
    recommendations=historical_recommendations,
    initial_cash=Decimal("100000.00"),
    confidence_threshold=0.70
)

# View results
print(f"Initial: ${result.initial_cash}")
print(f"Final: ${result.final_portfolio_value}")
print(f"Return: {result.performance_report.total_return_pct:.2f}%")
print(result.performance_report.to_text())
```

## Integration with Main System

The trading simulator is automatically integrated into the main analysis pipeline:

1. AnalysisEngine generates recommendations
2. TradingIntegration processes recommendations
3. Trades are executed based on confidence threshold
4. Performance is logged after each analysis cycle

The default portfolio is created on system startup with the configured initial cash balance.

## Position Sizing Strategies

### Percentage Strategy (Default)
Allocates a percentage of total portfolio value per trade.

Example: 10% strategy with $100,000 portfolio
- Trade size: $10,000
- If stock price is $50: Buy 200 shares

### Fixed Amount Strategy
Allocates a fixed dollar amount per trade.

Example: $5,000 fixed amount
- Always attempts to buy $5,000 worth
- If stock price is $50: Buy 100 shares

## Trade Validation

All trades are validated before execution:

- **Symbol format**: Must be valid stock symbol
- **Price**: Must be positive
- **Quantity**: Must be positive integer
- **Buy orders**: Sufficient cash balance required
- **Sell orders**: Sufficient position quantity required

Invalid trades are rejected with descriptive error messages.

## Performance Metrics

### Portfolio Metrics
- **Portfolio Value**: Cash + sum of position values
- **Cash Balance**: Available cash for trading
- **Total Positions**: Number of open positions

### P&L Metrics
- **Realized P&L**: Profit/loss from closed trades
- **Unrealized P&L**: Profit/loss from open positions
- **Total P&L**: Realized + Unrealized
- **Total Return %**: (Current Value - Initial) / Initial × 100

### Trade Statistics
- **Total Trades**: Number of trades executed
- **Win Rate**: Percentage of profitable trades
- **Avg Profit/Win**: Average profit per winning trade
- **Avg Loss/Loss**: Average loss per losing trade
- **Max Drawdown**: Largest peak-to-trough decline

## Data Persistence

### Trade History
All trades are persisted to `data/trade_history.json` with:
- Trade ID, portfolio ID, symbol
- Action (BUY/SELL), quantity, price
- Timestamp, recommendation ID

### Portfolio State
Portfolios can be saved/loaded as JSON:
- Portfolio ID, cash balance
- All positions with quantities and cost basis
- Creation timestamp, initial cash

## Error Handling

The system provides clear error messages for:
- Invalid trade parameters
- Insufficient cash or positions
- Missing portfolios
- Configuration errors
- Validation failures

## Best Practices

1. **Start with conservative position sizing** (5-10% of portfolio)
2. **Use appropriate confidence thresholds** (0.70-0.80 recommended)
3. **Monitor performance regularly** using performance reports
4. **Backtest strategies** before live simulation
5. **Save portfolio state** periodically
6. **Review trade history** to understand execution patterns

## Examples

See `examples/` directory for:
- `trading_simulation_example.py`: Basic usage examples
- `backtest_example.py`: Backtesting workflow

## Limitations

- Simulated trades use recommendation prices (no slippage modeling)
- No transaction costs or fees
- No short selling support
- No options or derivatives
- Simplified position sizing (whole shares only)

## Future Enhancements

Potential improvements:
- Transaction cost modeling
- Slippage simulation
- Short selling support
- Advanced position sizing (Kelly criterion, risk parity)
- Stop-loss and take-profit orders
- Portfolio rebalancing strategies
- Multi-portfolio management
- Real-time price updates
