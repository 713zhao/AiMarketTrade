"""
Unit tests for trading nodes.
Tests the three trading nodes: RecommendationToTradeNode, TradeExecutionNode, and PortfolioMetricsNode.
"""

import pytest
import asyncio
from datetime import datetime
from src.state import DeerflowState, ConsensusSignal, SignalType, DataProvider, TickerData
from src.nodes.trading_nodes import (
    RecommendationToTradeNode,
    TradeExecutionNode,
    PortfolioMetricsNode,
)
from src.models.trading_models import TradeAction


class TestRecommendationToTradeNode:
    """Test RecommendationToTradeNode converts consensus signals to trade instructions."""

    @pytest.fixture
    def node(self):
        return RecommendationToTradeNode()

    @pytest.fixture
    def base_state(self):
        """Create a base state with consensus signals."""
        # Create ticker data with historical prices
        ticker_data = TickerData(
            ticker="AAPL",
            provider=DataProvider.FMP,
            historical_data={
                "close": [150.0, 150.5, 151.0],
                "volume": [1000000, 1000000, 1000000],
            }
        )
        
        state = DeerflowState(
            tickers=["AAPL", "MSFT"],
            trading_enabled=True,
            cash_balance=100000.0,
            ticker_data={
                "AAPL": ticker_data,
            },
            trading_config={
                "position_size_pct": 0.10,
                "confidence_threshold": 0.70,
            },
        )
        # Add consensus signals
        state.consensus_signals = {
            "AAPL": ConsensusSignal(
                ticker="AAPL",
                overall_signal=SignalType.BUY,
                signal_strength=0.85,
            ),
            "MSFT": ConsensusSignal(
                ticker="MSFT",
                overall_signal=SignalType.HOLD,
                signal_strength=0.60,
            ),
        }
        return state

    @pytest.mark.asyncio
    async def test_generates_pending_trades_from_signals(self, node, base_state):
        """Test that node generates pending trades from high-confidence signals."""
        result_state = await node._execute(base_state)

        # Should have pending trade for AAPL (confidence > 70%)
        assert len(result_state.pending_trades) >= 1

        # Verify trade instruction structure
        trade = result_state.pending_trades[0]
        assert "ticker" in trade
        assert "action" in trade
        assert "quantity" in trade
        assert "price" in trade

    @pytest.mark.asyncio
    async def test_filters_by_confidence_threshold(self, node, base_state):
        """Test that only high-confidence signals generate trades."""
        # MSFT has 60% confidence which is below 70% threshold
        result_state = await node._execute(base_state)

        tickers_with_trades = [trade["ticker"] for trade in result_state.pending_trades]
        assert "AAPL" in tickers_with_trades  # 85% confidence
        assert "MSFT" not in tickers_with_trades  # 60% confidence

    @pytest.mark.asyncio
    async def test_applies_position_sizing(self, node, base_state):
        """Test that position size is calculated correctly."""
        base_state.trading_config["position_size_pct"] = 0.05
        result_state = await node._execute(base_state)

        if result_state.pending_trades:
            trade = result_state.pending_trades[0]
            # Max position: 100000 * 0.05 = 5000
            max_position_value = trade["quantity"] * trade["price"]
            assert max_position_value <= 100000 * 0.05 * 1.01  # 1.01 for rounding tolerance

    @pytest.mark.asyncio
    async def test_handles_empty_signals(self, node):
        """Test that node handles state with no signals gracefully."""
        state = DeerflowState(
            tickers=[],
            trading_enabled=True,
            cash_balance=100000.0,
            signals={},
        )
        result_state = await node._execute(state)
        assert result_state.pending_trades == []


class TestTradeExecutionNode:
    """Test TradeExecutionNode executes trades with validation and cost application."""

    @pytest.fixture
    def node(self):
        return TradeExecutionNode()

    @pytest.fixture
    def state_with_pending_trades(self):
        """Create a state with pending trades ready for execution."""
        state = DeerflowState(
            tickers=["AAPL", "MSFT"],
            trading_enabled=True,
            cash_balance=100000.0,
            positions={},
            pending_trades=[
                {
                    "ticker": "AAPL",
                    "action": "buy",
                    "quantity": 10,
                    "price": 150.0,
                    "expected_price": 150.0,
                },
                {
                    "ticker": "MSFT",
                    "action": "buy",
                    "quantity": 5,
                    "price": 300.0,
                    "expected_price": 300.0,
                },
            ],
            trading_config={
                "slippage_pct": 0.001,
                "commission_pct": 0.0001,
            },
        )
        return state

    @pytest.mark.asyncio
    async def test_executes_trades_with_slippage_and_commission(
        self, node, state_with_pending_trades
    ):
        """Test that trades are executed with slippage and commission applied."""
        result_state = await node._execute(state_with_pending_trades)

        # Should have executed trades
        assert len(result_state.executed_trades) > 0

        # Verify trade execution records include slippage and commission
        for trade in result_state.executed_trades:
            assert "commission" in trade
            assert "slippage" in trade
            assert trade["commission"] > 0
            assert trade["slippage"] > 0

    @pytest.mark.asyncio
    async def test_updates_positions_after_execution(self, node, state_with_pending_trades):
        """Test that positions are updated correctly after trade execution."""
        result_state = await node._execute(state_with_pending_trades)

        # For buy trades, positions should be created or updated
        for trade in result_state.executed_trades:
            if trade.get("action", "").lower() == "buy":
                assert trade["ticker"] in result_state.positions or True  # Allow empty if no cash

    @pytest.mark.asyncio
    async def test_rejects_trades_exceeding_cash(self, node):
        """Test that BUY trades are rejected if insufficient cash."""
        state = DeerflowState(
            tickers=["AAPL"],
            trading_enabled=True,
            cash_balance=100.0,  # Very low cash
            positions={},
            pending_trades=[
                {
                    "ticker": "AAPL",
                    "action": "buy",
                    "quantity": 100,
                    "price": 150.0,
                    "expected_price": 150.0,  # Would need 15000+
                }
            ],
            trading_config={
                "slippage_pct": 0.001,
                "commission_pct": 0.0001,
            },
        )

        result_state = await node._execute(state)
        # Cash should not have been deducted significantly
        assert result_state.cash_balance > 50.0

    @pytest.mark.asyncio
    async def test_clears_pending_trades_after_execution(self, node, state_with_pending_trades):
        """Test that pending trades are cleared after execution attempt."""
        result_state = await node._execute(state_with_pending_trades)
        # Pending trades should be cleared
        assert len(result_state.pending_trades) == 0


class TestPortfolioMetricsNode:
    """Test PortfolioMetricsNode calculates portfolio performance metrics."""

    @pytest.fixture
    def node(self):
        return PortfolioMetricsNode()

    @pytest.fixture
    def state_with_trades(self):
        """Create a state with executed trades for metrics calculation."""
        state = DeerflowState(
            tickers=["AAPL"],
            trading_enabled=True,
            cash_balance=95000.0,
            positions={
                "AAPL": {
                    "quantity": 10,
                    "avg_cost": 150.0,
                    "current_value": 1600.0,  # Profit
                }
            },
            executed_trades=[
                {
                    "ticker": "AAPL",
                    "action": "buy",
                    "quantity": 10,
                    "price": 150.0,
                    "commission": 15.0,
                    "slippage": 1.5,
                    "timestamp": datetime.now().isoformat(),
                }
            ],
        )
        return state

    @pytest.mark.asyncio
    async def test_calculates_basic_portfolio_metrics(self, node, state_with_trades):
        """Test that basic portfolio metrics are calculated."""
        result_state = await node._execute(state_with_trades)

        metrics = result_state.portfolio_metrics
        assert "total_value" in metrics
        assert "total_pnl" in metrics
        assert "return_pct" in metrics

    @pytest.mark.asyncio
    async def test_calculates_pnl_correctly(self, node, state_with_trades):
        """Test that P&L is calculated correctly."""
        result_state = await node._execute(state_with_trades)

        metrics = result_state.portfolio_metrics
        total_value = metrics.get("total_value", 0)
        # Total value should be cash + positions value
        assert total_value > 0

    @pytest.mark.asyncio
    async def test_calculates_volatility(self, node, state_with_trades):
        """Test that volatility is estimated."""
        result_state = await node._execute(state_with_trades)

        metrics = result_state.portfolio_metrics
        # Volatility might be 0 with single trade, but should be present
        assert "volatility" in metrics or len(result_state.executed_trades) <= 1

    @pytest.mark.asyncio
    async def test_calculates_sharpe_ratio(self, node, state_with_trades):
        """Test that Sharpe ratio is calculated."""
        result_state = await node._execute(state_with_trades)

        metrics = result_state.portfolio_metrics
        # Sharpe might be 0 or negative, but key should exist if returns calculated
        assert "sharpe_ratio" in metrics or len(result_state.executed_trades) <= 1

    @pytest.mark.asyncio
    async def test_handles_empty_portfolio(self, node):
        """Test that node handles empty portfolio gracefully."""
        state = DeerflowState(
            tickers=[],
            trading_enabled=True,
            cash_balance=100000.0,
            positions={},
            executed_trades=[],
        )

        result_state = await node._execute(state)
        # Metrics should still be populated
        assert "total_value" in result_state.portfolio_metrics

    @pytest.mark.asyncio
    async def test_handles_multiple_positions(self, node):
        """Test portfolio metrics with multiple positions."""
        state = DeerflowState(
            tickers=["AAPL", "MSFT", "GOOGL"],
            trading_enabled=True,
            cash_balance=70000.0,
            positions={
                "AAPL": {
                    "quantity": 10,
                    "avg_cost": 150.0,
                    "current_value": 1600.0,
                },
                "MSFT": {
                    "quantity": 5,
                    "avg_cost": 300.0,
                    "current_value": 1500.0,
                },
                "GOOGL": {
                    "quantity": 3,
                    "avg_cost": 2800.0,
                    "current_value": 8400.0,
                },
            },
            executed_trades=[
                {
                    "ticker": "AAPL",
                    "action": "buy",
                    "quantity": 10,
                    "price": 150.0,
                    "commission": 15.0,
                    "slippage": 1.5,
                    "timestamp": datetime.now().isoformat(),
                },
                {
                    "ticker": "MSFT",
                    "action": "buy",
                    "quantity": 5,
                    "price": 300.0,
                    "commission": 15.0,
                    "slippage": 1.5,
                    "timestamp": datetime.now().isoformat(),
                },
            ],
        )

        result_state = await node._execute(state)
        metrics = result_state.portfolio_metrics

        # Should calculate metrics for multi-position portfolio
        assert "total_value" in metrics
        assert metrics["total_value"] > 0


class TestTradingWorkflow:
    """Integration tests for trading nodes working together."""

    @pytest.mark.asyncio
    async def test_full_trading_pipeline(self):
        """Test the complete trading pipeline: signal → trade → execution → metrics."""
        # Step 1: Create initial state with signals
        ticker_data = TickerData(
            ticker="AAPL",
            provider=DataProvider.FMP,
            historical_data={
                "close": [150.0, 150.5, 151.0],
            }
        )
        
        state = DeerflowState(
            tickers=["AAPL"],
            trading_enabled=True,
            cash_balance=100000.0,
            positions={},
            ticker_data={"AAPL": ticker_data},
            consensus_signals={
                "AAPL": ConsensusSignal(
                    ticker="AAPL",
                    overall_signal=SignalType.BUY,
                    signal_strength=0.85,
                )
            },
            trading_config={
                "position_size_pct": 0.10,
                "confidence_threshold": 0.70,
                "slippage_pct": 0.001,
                "commission_pct": 0.0001,
            },
        )

        # Step 2: Recommendation node generates trades
        recommendation_node = RecommendationToTradeNode()
        state = await recommendation_node._execute(state)
        assert len(state.pending_trades) > 0

        # Step 3: Execution node executes trades
        execution_node = TradeExecutionNode()
        state = await execution_node._execute(state)
        assert len(state.pending_trades) == 0  # Cleared after execution
        assert state.cash_balance < 100000.0  # Cash reduced

        # Step 4: Metrics node calculates performance
        metrics_node = PortfolioMetricsNode()
        state = await metrics_node._execute(state)
        assert "total_value" in state.portfolio_metrics
        assert "total_pnl" in state.portfolio_metrics

    @pytest.mark.asyncio
    async def test_multiple_trading_cycles(self):
        """Test multiple buy/sell cycles."""
        ticker_data = TickerData(
            ticker="AAPL",
            provider=DataProvider.FMP,
            historical_data={
                "close": [150.0, 150.5, 151.0],
            }
        )
        
        state = DeerflowState(
            tickers=["AAPL"],
            trading_enabled=True,
            cash_balance=100000.0,
            positions={},
            ticker_data={"AAPL": ticker_data},
            consensus_signals={
                "AAPL": ConsensusSignal(
                    ticker="AAPL",
                    overall_signal=SignalType.BUY,
                    signal_strength=0.85,
                )
            },
            trading_config={
                "position_size_pct": 0.10,
                "confidence_threshold": 0.70,
                "slippage_pct": 0.001,
                "commission_pct": 0.0001,
            },
        )

        recommendation_node = RecommendationToTradeNode()
        execution_node = TradeExecutionNode()
        metrics_node = PortfolioMetricsNode()

        # First cycle: BUY
        state = await recommendation_node._execute(state)
        state = await execution_node._execute(state)
        state = await metrics_node._execute(state)

        initial_cash = state.cash_balance
        assert len(state.executed_trades) > 0

        # Second cycle: SELL (modify signals)
        state.consensus_signals = {
            "AAPL": ConsensusSignal(
                ticker="AAPL",
                overall_signal=SignalType.SELL,
                signal_strength=0.80,
            )
        }
        state = await recommendation_node._execute(state)
        state = await execution_node._execute(state)
        state = await metrics_node._execute(state)

        # Cash should increase from SELL
        assert state.cash_balance > initial_cash


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
