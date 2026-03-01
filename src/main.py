#!/usr/bin/env python3
"""
Main entry point for deerflow-openbb trading system.

Provides command-line interface for running analysis with configurable
tickers, modes, and output formats.
"""

import argparse
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings, reload_settings
from src.graph import create_mock_graph, create_deerflow_graph, print_state_summary
from src.state import DeerflowState


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Deerflow + OpenBB Multi-Agent Trading System (Phase 2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Phase 2: Multi-Agent Expansion with Parallel Execution

This version implements 6 analyst nodes running in parallel:
  - Technical Analyst (price patterns, indicators)
  - Fundamentals Analyst (financial health, valuation)
  - Growth Analyst (future potential)
  - News Analyst (sentiment, catalysts)
  - Macro Analyst (economic context)
  - Risk Analyst (volatility, drawdown, financial risk)

All signals converge to consensus, then produce final decision.

Examples:
  %(prog)s AAPL MSFT GOOGL              # Auto mode (live if keys, else mock)
  %(prog)s AAPL --mode mock              # Force mock data
  %(prog)s --tickers AAPL,AMZN,NVDA --output json
  %(prog)s --check-config                # Validate configuration
  %(prog)s AAPL --full-pipeline --output summary
        """
    )

    # Tickers (positional or via flag)
    parser.add_argument(
        'tickers',
        nargs='*',
        help='Stock ticker symbols to analyze (e.g., AAPL MSFT GOOGL)'
    )
    parser.add_argument(
        '--tickers', '-t',
        type=str,
        help='Comma-separated list of tickers'
    )

    # Analysis mode
    parser.add_argument(
        '--mode', '-m',
        choices=['live', 'mock', 'auto'],
        default='auto',
        help='Analysis mode: live uses real APIs, mock uses synthetic data, auto detects (default)'
    )

    # Output format
    parser.add_argument(
        '--output', '-o',
        choices=['summary', 'json', 'csv', 'silent'],
        default='summary',
        help='Output format (default: summary)'
    )

    # Output file
    parser.add_argument(
        '--output-file',
        type=str,
        help='Write output to file'
    )

    # Configuration
    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom config file (not yet implemented)'
    )
    parser.add_argument(
        '--check-config',
        action='store_true',
        help='Validate configuration and exit'
    )

    # Feature flags
    parser.add_argument(
        '--full-pipeline',
        action='store_true',
        help='Use all 6 analyst nodes (default in Phase 2)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose logging'
    )

    return parser.parse_args()


def validate_configuration():
    """Validate configuration and print status."""
    settings = get_settings()

    print("Configuration Validation")
    print("-" * 50)

    # Check data providers
    available_providers = settings.get_available_data_providers()
    primary_provider = settings.get_primary_data_provider()

    print(f"Primary data provider: {primary_provider}")

    requires_key = settings.requires_api_key(primary_provider)
    api_key = getattr(settings, f"{primary_provider}_api_key", None)
    if requires_key and not api_key:
        print(f"  WARNING: {primary_provider.upper()} API key NOT configured!")
    else:
        print(f"  ✓ API key configured for {primary_provider}")

    # Check LLM provider
    llm_configured = False
    if settings.openai_api_key:
        print(f"✓ OpenAI API key configured (model: {settings.default_llm_model})")
        llm_configured = True
    elif settings.anthropic_api_key:
        print(f"✓ Anthropic API key configured")
        llm_configured = True
    else:
        print("⚠ No LLM API keys configured (analysis will use rule-based methods)")

    print("\nAvailable data providers:")
    for provider in available_providers:
        print(f"  ✓ {provider}")

    print("\nConfiguration status: " + ("✅ OK" if (api_key or primary_provider == 'yahoo') else "⚠ INCOMPLETE"))
    print("  (Mock mode works without API keys)")
    return True


def output_results(
    state: DeerflowState,
    format: str = 'summary',
    output_file: str = None
) -> None:
    """Format and output analysis results."""
    output = ""

    if format == 'summary':
        print_state_summary(state)
        return

    elif format == 'json':
        output = state.model_dump(
            exclude={'ticker_data'},
            exclude_none=True,
            warnings=False
        )
        output['ticker_summaries'] = {}
        for ticker, ticker_data in state.ticker_data.items():
            output['ticker_summaries'][ticker] = {
                'data_quality_score': ticker_data.data_quality_score,
                'has_historical_data': bool(ticker_data.historical_data),
                'has_fundamentals': bool(ticker_data.financial_statements),
                'has_news': len(ticker_data.news),
            }
        output = json.dumps(output, indent=2, default=str)

    elif format == 'csv':
        import csv
        import io
        output_stream = io.StringIO()
        writer = csv.writer(output_stream)
        writer.writerow(['Ticker', 'Signal', 'Position_Size', 'Confidence', 'Stop_Loss', 'Take_Profit', 'Rationale'])
        for ticker in state.tickers:
            decision = state.trading_decisions.get(ticker)
            if decision:
                writer.writerow([
                    ticker,
                    decision.action.value,
                    f"{decision.position_size:.2f}%",
                    f"{decision.confidence:.2%}",
                    f"{decision.stop_loss:.2f}" if decision.stop_loss else "",
                    f"{decision.take_profit:.2f}" if decision.take_profit else "",
                    decision.rationale[:150].replace('\n', ' ')
                ])
        output = output_stream.getvalue()

    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"Results written to {output_file}")
    else:
        print(output)


async def main_async(args) -> int:
    """Async main execution."""
    try:
        # Configuration
        if args.config:
            print(f"Note: Custom config file {args.config} not yet implemented, using defaults")
        settings = reload_settings()

        # Validation only
        if args.check_config:
            validate_configuration()
            return 0

        # Determine tickers
        tickers = []
        if args.tickers:
            tickers = [t.strip().upper() for t in args.tickers.split(',')]
        elif not args.tickers:
            tickers = settings.default_tickers
            print(f"Using default tickers: {', '.join(tickers)}")

        # Validate tickers
        tickers = [t.upper() for t in tickers]
        if len(tickers) > 10:
            print("WARNING: Too many tickers. Limiting to 10.")
            tickers = tickers[:10]

        print(f"\n{'='*60}")
        print(f"DEERFLOW PHASE 2 - MULTI-AGENT ANALYSIS")
        print(f"{'='*60}")
        print(f"Mode: {args.mode}")
        print(f"Tickers: {', '.join(tickers)}")
        print(f"Full Pipeline: {'Enabled' if args.full_pipeline else 'Disabled (fallback)'}")
        print()

        # Select graph
        if args.mode == 'mock':
            print("🔬 Using MOCK data (synthetic)")
            graph = create_mock_graph()
        else:  # live or auto
            provider = settings.get_primary_data_provider()
            requires_key = settings.requires_api_key(provider)
            api_key = getattr(settings, f"{provider}_api_key", None)

            if requires_key and not api_key:
                print(f"⚠️  {provider.upper()} API key not configured.")
                print("   Falling back to MOCK data.")
                print("   To use live data, add API keys to .env file")
                graph = create_mock_graph()
            else:
                print(f"📡 Using live data provider: {provider}")
                graph = create_deerflow_graph()

        # Prepare initial state
        from src.state import DeerflowState
        from uuid import uuid4

        initial_state = DeerflowState(
            session_id=str(uuid4()),
            tickers=tickers,
            analysis_scope={
                "time_horizon": settings.time_horizon,
                "risk_tolerance": settings.risk_tolerance,
                "max_position_size": settings.max_position_size,
            }
        )

        # Execute graph
        print("\n[Graph] Starting analysis workflow...")
        print("[Graph] Nodes: stock_data → [technical, fundamentals, news, growth, macro, risk] → consensus → decision")
        start_time = datetime.utcnow()

        result = graph.invoke(initial_state, {
            "configurable": {"thread_id": initial_state.session_id}
        })

        execution_time = (datetime.utcnow() - start_time).total_seconds()
        result.execution_time = execution_time
        state = result

        # Output results
        print("\n" + "="*80)
        output_results(state, format=args.output, output_file=args.output_file)

        # Summary
        print("📊 EXECUTION SUMMARY")
        print(f"   Tickers analyzed: {len(state.tickers)}")
        print(f"   Data quality: {sum(d.data_quality_score for d in state.ticker_data.values())/len(state.ticker_data):.1%}")
        print(f"   Decisions made: {len(state.trading_decisions)}")
        print(f"   Execution time: {execution_time:.2f}s")
        if state.errors:
            print(f"   Errors: {len(state.errors)} (see above)")

        print(f"\n✅ Analysis complete!")
        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    args = parse_arguments()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
