"""
CLI interface for trading simulation.
"""

import argparse
import sys
from decimal import Decimal
from pathlib import Path

from stock_market_analysis.components.configuration_manager import ConfigurationManager
from .trading_simulator import TradingSimulator
from .backtest_engine import BacktestEngine


def create_portfolio_command(args):
    """Creates a new portfolio."""
    config_manager = ConfigurationManager()
    simulator = TradingSimulator(config_manager)
    
    initial_cash = Decimal(str(args.initial_cash))
    portfolio_id = simulator.create_portfolio(initial_cash)
    
    print(f"✓ Created portfolio: {portfolio_id}")
    print(f"  Initial cash: ${initial_cash:,.2f}")
    
    # Save portfolio if path provided
    if args.save:
        simulator.save_portfolio(portfolio_id, args.save)
        print(f"  Saved to: {args.save}")


def deposit_cash_command(args):
    """Deposits cash into a portfolio."""
    config_manager = ConfigurationManager()
    simulator = TradingSimulator(config_manager)
    
    # Load portfolio
    portfolio_id = simulator.load_portfolio(args.portfolio_file)
    
    # Deposit cash
    amount = Decimal(str(args.amount))
    simulator.deposit_cash(portfolio_id, amount)
    
    portfolio = simulator.get_portfolio(portfolio_id)
    print(f"✓ Deposited ${amount:,.2f}")
    print(f"  New balance: ${portfolio.cash_balance:,.2f}")
    
    # Save portfolio
    simulator.save_portfolio(portfolio_id, args.portfolio_file)
    print(f"  Saved to: {args.portfolio_file}")


def execute_trade_command(args):
    """Executes a manual trade."""
    config_manager = ConfigurationManager()
    simulator = TradingSimulator(config_manager)
    
    # Load portfolio
    portfolio_id = simulator.load_portfolio(args.portfolio_file)
    
    # Execute trade
    price = Decimal(str(args.price))
    trade = simulator.execute_trade(
        portfolio_id,
        args.symbol,
        args.action,
        args.quantity,
        price
    )
    
    print(f"✓ Executed {trade.action.value}: {trade.quantity} {trade.symbol} @ ${trade.price}")
    
    portfolio = simulator.get_portfolio(portfolio_id)
    print(f"  Cash balance: ${portfolio.cash_balance:,.2f}")
    
    # Save portfolio
    simulator.save_portfolio(portfolio_id, args.portfolio_file)
    print(f"  Saved to: {args.portfolio_file}")


def view_portfolio_command(args):
    """Views portfolio details."""
    config_manager = ConfigurationManager()
    simulator = TradingSimulator(config_manager)
    
    # Load portfolio
    portfolio_id = simulator.load_portfolio(args.portfolio_file)
    portfolio = simulator.get_portfolio(portfolio_id)
    
    print("=" * 60)
    print("PORTFOLIO DETAILS")
    print("=" * 60)
    print(f"Portfolio ID: {portfolio.portfolio_id}")
    print(f"Cash Balance: ${portfolio.cash_balance:,.2f}")
    print(f"Initial Cash: ${portfolio.initial_cash_balance:,.2f}")
    print(f"Created: {portfolio.creation_timestamp}")
    print()
    
    if portfolio.positions:
        print("POSITIONS:")
        print("-" * 60)
        for symbol, position in portfolio.positions.items():
            value = position.calculate_value(position.average_cost_basis)
            print(f"{symbol:8} | Qty: {position.quantity:6} | "
                  f"Avg Cost: ${position.average_cost_basis:>8,.2f} | "
                  f"Value: ${value:>10,.2f}")
    else:
        print("No open positions")
    
    print("=" * 60)


def view_performance_command(args):
    """Views performance report."""
    config_manager = ConfigurationManager()
    simulator = TradingSimulator(config_manager)
    
    # Load portfolio
    portfolio_id = simulator.load_portfolio(args.portfolio_file)
    
    # Generate report
    report = simulator.get_performance_report(portfolio_id)
    
    # Display report
    if args.format == 'text':
        print(report.to_text())
    else:  # json
        print(report.to_json())


def run_backtest_command(args):
    """Runs a backtest."""
    print("Backtest functionality requires historical recommendations data.")
    print("This is a placeholder for backtest execution.")
    print()
    print("To run a backtest:")
    print("1. Prepare historical recommendations in JSON format")
    print("2. Use the BacktestEngine programmatically")
    print("3. See examples/backtest_example.py for details")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Trading Simulation CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create portfolio command
    create_parser = subparsers.add_parser('create-portfolio', help='Create a new portfolio')
    create_parser.add_argument('initial_cash', type=float, help='Initial cash balance')
    create_parser.add_argument('--save', type=str, help='Save portfolio to file')
    create_parser.set_defaults(func=create_portfolio_command)
    
    # Deposit cash command
    deposit_parser = subparsers.add_parser('deposit', help='Deposit cash into portfolio')
    deposit_parser.add_argument('portfolio_file', type=str, help='Portfolio file path')
    deposit_parser.add_argument('amount', type=float, help='Amount to deposit')
    deposit_parser.set_defaults(func=deposit_cash_command)
    
    # Execute trade command
    trade_parser = subparsers.add_parser('trade', help='Execute a manual trade')
    trade_parser.add_argument('portfolio_file', type=str, help='Portfolio file path')
    trade_parser.add_argument('action', choices=['BUY', 'SELL'], help='Trade action')
    trade_parser.add_argument('symbol', type=str, help='Stock symbol')
    trade_parser.add_argument('quantity', type=int, help='Number of shares')
    trade_parser.add_argument('price', type=float, help='Price per share')
    trade_parser.set_defaults(func=execute_trade_command)
    
    # View portfolio command
    view_parser = subparsers.add_parser('view-portfolio', help='View portfolio details')
    view_parser.add_argument('portfolio_file', type=str, help='Portfolio file path')
    view_parser.set_defaults(func=view_portfolio_command)
    
    # View performance command
    perf_parser = subparsers.add_parser('view-performance', help='View performance report')
    perf_parser.add_argument('portfolio_file', type=str, help='Portfolio file path')
    perf_parser.add_argument('--format', choices=['text', 'json'], default='text',
                            help='Output format')
    perf_parser.set_defaults(func=view_performance_command)
    
    # Run backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run a backtest')
    backtest_parser.set_defaults(func=run_backtest_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
