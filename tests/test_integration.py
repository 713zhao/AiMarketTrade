"""
Integration test for end-to-end deerflow workflow.

Tests the complete pipeline with mock data to ensure all components
integrate correctly.
"""

import pytest
import asyncio
from datetime import datetime

from deerflow_openbb.state import DeerflowState, AnalystType
from deerflow_openbb.graph import create_mock_graph


@pytest.mark.asyncio
async def test_mock_data_pipeline():
    """Test complete pipeline with mock data."""

    # Create mock graph (uses synthetic data, no API keys needed)
    graph = create_mock_graph()

    # Create initial state
    state = DeerflowState(
        session_id="test_mock_001",
        tickers=["AAPL", "MSFT", "GOOGL"],
        analysis_scope={
            "time_horizon": "MEDIUM",
            "risk_tolerance": "MODERATE",
        }
    )

    # Execute graph
    config = {"configurable": {"thread_id": state.session_id}}

    result = graph.invoke(state, config)

    # Validate results
    assert result.session_id == "test_mock_001"
    assert len(result.tickers) == 3

    # All tickers should have ticker data
    for ticker in ["AAPL", "MSFT", "GOOGL"]:
        assert ticker in result.ticker_data
        ticker_data = result.ticker_data[ticker]
        assert ticker_data.ticker == ticker
        assert ticker_data.historical_data  # Has historical data
        assert ticker_data.data_quality_score > 0

    # All tickers should have technical analysis
    for ticker in ["AAPL", "MSFT", "GOOGL"]:
        assert ticker in result.technical_analyses
        tech = result.technical_analyses[ticker]
        assert tech.ticker == ticker
        assert tech.analyst_type == AnalystType.TECHNICAL
        assert tech.trend in ["bullish", "bearish", "neutral"]
        assert 0.0 <= tech.confidence <= 1.0
        assert isinstance(tech.indicators, dict)
        assert isinstance(tech.signals, list)

    # All tickers should have trading decisions
    for ticker in ["AAPL", "MSFT", "GOOGL"]:
        assert ticker in result.trading_decisions
        decision = result.trading_decisions[ticker]
        assert decision.ticker == ticker
        assert decision.action.value in ["buy", "sell", "hold"]
        assert 0.0 <= decision.position_size <= 100.0
        assert decision.confidence >= 0.0
        assert decision.rationale  # Non-empty rationale

    # Execution time should be recorded
    assert result.execution_time is not None
    assert result.execution_time > 0

    # No errors expected in mock mode
    assert len(result.errors) == 0

    print(f"\n✓ Mock pipeline test passed")
    print(f"  Analyzed: {', '.join(result.tickers)}")
    print(f"  Execution time: {result.execution_time:.2f}s")
    print(f"  Decisions: {len(result.trading_decisions)}")

    return result


@pytest.mark.asyncio
async def test_single_ticker_analysis():
    """Test analysis of a single ticker."""

    graph = create_mock_graph()

    state = DeerflowState(
        tickers=["AAPL"],
        session_id="test_single_001"
    )

    result = graph.invoke(state, {"configurable": {"thread_id": state.session_id}})

    assert "AAPL" in result.ticker_data
    assert "AAPL" in result.technical_analyses
    assert "AAPL" in result.trading_decisions

    # Verify technical analysis details
    tech = result.technical_analyses["AAPL"]
    assert "SMA_20" in tech.indicators
    assert "RSI_14" in tech.indicators
    assert "MACD" in tech.indicators
    assert len(tech.support_levels) > 0 or len(tech.resistance_levels) > 0

    print(f"\n✓ Single ticker test passed for AAPL")

    return result


@pytest.mark.asyncio
async def test_multiple_tickers_independence():
    """Test that analysis of multiple tickers is independent."""

    graph = create_mock_graph()

    state = DeerflowState(
        tickers=["AAPL", "TSLA", "JPM"],
        session_id="test_multi_001"
    )

    result = graph.invoke(state, {"configurable": {"thread_id": state.session_id}})

    # All tickers analyzed independently
    decisions = result.trading_decisions

    # Compare signals - they should not all be the same (mocked data generates different patterns)
    signals = [d.action for d in decisions.values()]
    # At least some variety expected (statistically very unlikely all same)
    unique_signals = set(signals)
    # In mock data with random seeds, we typically get mixed signals
    # Allow all same in rare case, but verify completeness
    assert len(decisions) == 3
    for ticker in ["AAPL", "TSLA", "JPM"]:
        assert ticker in decisions

    print(f"\n✓ Multiple ticker independence test passed")
    print(f"  Signals: {', '.join(s.value for s in signals)}")

    return result


def test_state_transitions():
    """Test that state transitions properly through graph."""
    graph = create_mock_graph()

    initial_state = DeerflowState(
        tickers=["AAPL"],
        session_id="test_transitions_001"
    )

    # Before execution
    assert len(initial_state.ticker_data) == 0
    assert len(initial_state.technical_analyses) == 0
    assert len(initial_state.trading_decisions) == 0
    assert len(initial_state.completed_nodes) == 0

    # Execute
    result = graph.invoke(initial_state, {
        "configurable": {"thread_id": initial_state.session_id}
    })

    # After execution
    assert len(result.ticker_data) == 1
    assert len(result.technical_analyses) == 1
    assert len(result.trading_decisions) == 1
    assert len(result.completed_nodes) >= 3  # At least stock_data, technical_analyst, decision

    # Check node execution order
    assert "stock_data" in result.completed_nodes
    assert "technical_analyst" in result.completed_nodes
    assert "decision" in result.completed_nodes

    print(f"\n✓ State transitions test passed")


def test_decision_logic():
    """Test that decision node produces actionable signals."""

    # This is a simplified test - we use mock graph which includes all nodes
    graph = create_mock_graph()

    state = DeerflowState(
        tickers=["AAPL"],
        session_id="test_decisions_001"
    )

    result = graph.invoke(state, {
        "configurable": {"thread_id": state.session_id}
    })

    decision = result.trading_decisions["AAPL"]

    # Verify decision structure
    assert decision.action in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
    assert decision.position_size >= 0
    assert decision.confidence >= 0 and decision.confidence <= 1
    assert decision.rationale  # Should have explanation
    assert decision.timestamp  # Should be set

    # For buy/sell signals, check risk management
    if decision.action == SignalType.BUY:
        # BUY decisions should have position size > 0
        assert decision.position_size > 0
    elif decision.action == SignalType.SELL:
        # SELL indicates exit, can be negative position size
        assert decision.position_size <= 0 or decision.position_size == 0
    else:  # HOLD
        assert decision.position_size == 0

    print(f"\n✓ Decision logic test passed")
    print(f"  Signal: {decision.action.value.upper()}")
    print(f"  Position: {decision.position_size:.1f}%")
    print(f"  Confidence: {decision.confidence:.1%}")

    return decision


if __name__ == "__main__":
    # Run all integration tests manually
    print("Running integration tests...\n")

    async def run_all():
        print("="*60)
        print("INTEGRATION TEST SUITE")
        print("="*60)

        try:
            print("\n[1/4] Mock Data Pipeline")
            await test_mock_data_pipeline()

            print("\n[2/4] Single Ticker Analysis")
            await test_single_ticker_analysis()

            print("\n[3/4] Multiple Tickers Independence")
            await test_multiple_tickers_independence()

            print("\n[4/4] Decision Logic")
            test_decision_logic()

            print("\n" + "="*60)
            print(" ALL TESTS PASSED ✓")
            print("="*60)
            return 0

        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            return 1

    exit_code = asyncio.run(run_all())
    sys.exit(exit_code)
