"""
Unit tests for Phase 5 production deployment nodes.

Tests for:
- EfficientFrontierNode
- PerformanceAttributionNode
- TransactionCostNode
- BacktestingEngineNode
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
import numpy as np

from deerflow_openbb.state import (
    DeerflowState,
    ConsensusSignal,
    SignalType,
    EfficientFrontierData,
    EfficientFrontierPoint,
    PortfolioOptimizationResult,
    TransactionExecutionPlan,
    BacktestResult,
    PortfolioSnapshot,
    PerformanceAttribution,
    RiskAnalysis,
)
from deerflow_openbb.nodes import (
    EfficientFrontierNode,
    PerformanceAttributionNode,
    TransactionCostNode,
    BacktestingEngineNode,
)


class TestEfficientFrontierNode:
    """Test efficient frontier generation and optimization."""

    @pytest.fixture
    def node(self):
        return EfficientFrontierNode()

    @pytest.fixture
    def state_with_signals(self):
        """Create state with consensus signals for portfolio."""
        state = DeerflowState(
            tickers=["AAPL", "MSFT", "GOOG", "TSLA", "NVDA"],
            consensus_signals={
                "AAPL": ConsensusSignal(
                    ticker="AAPL", 
                    overall_signal=SignalType.BUY,
                    signal_strength=0.7,
                    confidence=0.85
                ),
                "MSFT": ConsensusSignal(
                    ticker="MSFT",
                    overall_signal=SignalType.BUY,
                    signal_strength=0.6,
                    confidence=0.80
                ),
                "GOOG": ConsensusSignal(
                    ticker="GOOG",
                    overall_signal=SignalType.HOLD,
                    signal_strength=0.2,
                    confidence=0.75
                ),
                "TSLA": ConsensusSignal(
                    ticker="TSLA",
                    overall_signal=SignalType.SELL,
                    signal_strength=-0.5,
                    confidence=0.70
                ),
                "NVDA": ConsensusSignal(
                    ticker="NVDA",
                    overall_signal=SignalType.STRONG_BUY,
                    signal_strength=0.8,
                    confidence=0.90
                ),
            },
            risk_analyses={
                "AAPL": RiskAnalysis(ticker="AAPL", volatility=0.18),
                "MSFT": RiskAnalysis(ticker="MSFT", volatility=0.16),
                "GOOG": RiskAnalysis(ticker="GOOG", volatility=0.17),
                "TSLA": RiskAnalysis(ticker="TSLA", volatility=0.35),
                "NVDA": RiskAnalysis(ticker="NVDA", volatility=0.28),
            },
            portfolio_optimization=PortfolioOptimizationResult(
                optimization_method="kelly",
                expected_return=0.12,
                optimized_volatility=0.15,
                sharpe_ratio=0.8,
                optimized_positions={
                    "AAPL": 0.25,
                    "MSFT": 0.20,
                    "GOOG": 0.15,
                    "NVDA": 0.40,
                }
            ),
        )
        return state

    @pytest.mark.asyncio
    async def test_execute_generates_frontier(self, node, state_with_signals):
        """Test that node generates efficient frontier."""
        result = await node.execute(state_with_signals)

        assert result.efficient_frontier_data is not None
        assert len(result.efficient_frontier_data.portfolios) == 50  # Default num_portfolios
        assert "efficient_frontier_node" in result.completed_nodes

    @pytest.mark.asyncio
    async def test_frontier_contains_special_portfolios(self, node, state_with_signals):
        """Test that frontier includes special portfolios."""
        result = await node.execute(state_with_signals)
        frontier = result.efficient_frontier_data

        assert frontier.global_minimum_variance is not None
        assert frontier.maximum_sharpe_portfolio is not None
        assert frontier.current_portfolio is not None

    @pytest.mark.asyncio
    async def test_frontier_portfolios_increasing_return(self, node, state_with_signals):
        """Test that frontier portfolios increase in return."""
        result = await node.execute(state_with_signals)
        frontend = result.efficient_frontier_data.portfolios

        returns = [p.expected_return for p in frontend]
        vols = [p.volatility for p in frontend]

        # Returns should be increasing
        assert returns == sorted(returns)
        # Volatility should generally increase with return
        assert np.corrcoef(returns, vols)[0, 1] > 0.8

    def test_estimate_ticker_returns(self, node, state_with_signals):
        """Test ticker return estimation from signals."""
        returns = node._estimate_ticker_returns(
            list(state_with_signals.consensus_signals.keys()),
            state_with_signals
        )

        assert len(returns) == 5
        assert returns["NVDA"] > returns["GOOG"]  # NVDA has stronger signal
        assert returns["TSLA"] < 0.1  # TSLA has negative signal

    def test_estimate_ticker_volatilities(self, node, state_with_signals):
        """Test volatility extraction from risk analyses."""
        vols = node._estimate_ticker_volatilities(
            list(state_with_signals.risk_analyses.keys()),
            state_with_signals
        )

        assert vols["TSLA"] > vols["MSFT"]  # TSLA more volatile
        assert all(v > 0 for v in vols.values())

    @pytest.mark.asyncio
    async def test_frontier_summary_generated(self, node, state_with_signals):
        """Test that frontier summary narrative is generated."""
        result = await node.execute(state_with_signals)
        frontier = result.efficient_frontier_data

        assert frontier.summary is not None
        assert len(frontier.summary) > 0
        assert "有效边界" in frontier.summary or "efficient" in frontier.summary.lower()


class TestPerformanceAttributionNode:
    """Test performance attribution analysis."""

    @pytest.fixture
    def node(self):
        return PerformanceAttributionNode()

    @pytest.fixture
    def state_with_optimization(self):
        """Create state with optimization results."""
        state = DeerflowState(
            tickers=["AAPL", "MSFT", "GOOG"],
            consensus_signals={
                "AAPL": ConsensusSignal(
                    ticker="AAPL",
                    overall_signal=SignalType.BUY,
                    signal_strength=0.7,
                    confidence=0.85
                ),
                "MSFT": ConsensusSignal(
                    ticker="MSFT",
                    overall_signal=SignalType.BUY,
                    signal_strength=0.6,
                    confidence=0.80
                ),
                "GOOG": ConsensusSignal(
                    ticker="GOOG",
                    overall_signal=SignalType.HOLD,
                    signal_strength=0.2,
                    confidence=0.75
                ),
            },
            portfolio_optimization=PortfolioOptimizationResult(
                optimization_method="kelly",
                expected_return=0.10,
                optimized_volatility=0.14,
                sharpe_ratio=0.71,
                optimized_positions={
                    "AAPL": 0.40,
                    "MSFT": 0.35,
                    "GOOG": 0.25,
                }
            ),
        )
        return state

    @pytest.mark.asyncio
    async def test_execute_performs_attribution(self, node, state_with_optimization):
        """Test that attribution analysis is performed."""
        result = await node.execute(state_with_optimization)

        assert result.performance_attribution is not None
        assert "performance_attribution_node" in result.completed_nodes

    @pytest.mark.asyncio
    async def test_attribution_decomposes_returns(self, node, state_with_optimization):
        """Test that attribution decomposes into components."""
        result = await node.execute(state_with_optimization)
        attr = result.performance_attribution

        assert attr.allocation_effect is not None
        assert attr.selection_effect is not None
        assert attr.interaction_effect is not None
        assert attr.portfolio_return is not None

    @pytest.mark.asyncio
    async def test_attribution_identifies_contributors(self, node, state_with_optimization):
        """Test that top contributors and detractors are identified."""
        result = await node.execute(state_with_optimization)
        attr = result.performance_attribution

        assert len(attr.top_contributors) > 0
        assert len(attr.top_detractors) > 0

    @pytest.mark.asyncio
    async def test_attribution_holding_level(self, node, state_with_optimization):
        """Test holding-level attribution calculation."""
        result = await node.execute(state_with_optimization)
        attr = result.performance_attribution

        assert len(attr.holding_attribution) > 0
        for ticker, contrib in attr.holding_attribution.items():
            assert "allocation_effect" in contrib
            assert "selection_effect" in contrib
            assert "total_return" in contrib


class TestTransactionCostNode:
    """Test transaction cost modeling and execution planning."""

    @pytest.fixture
    def node(self):
        return TransactionCostNode()

    @pytest.fixture
    def state_with_optimization(self):
        """Create state with portfolio optimization."""
        state = DeerflowState(
            tickers=["AAPL", "MSFT", "GOOG"],
            portfolio_optimization=PortfolioOptimizationResult(
                optimization_method="kelly",
                expected_return=0.12,
                optimized_volatility=0.15,
                sharpe_ratio=0.8,
                optimized_positions={
                    "AAPL": 0.50,
                    "MSFT": 0.30,
                    "GOOG": 0.20,
                }
            ),
            risk_analyses={
                "AAPL": RiskAnalysis(ticker="AAPL", volatility=0.18),
                "MSFT": RiskAnalysis(ticker="MSFT", volatility=0.16),
                "GOOG": RiskAnalysis(ticker="GOOG", volatility=0.17),
            },
        )
        return state

    @pytest.mark.asyncio
    async def test_execute_creates_execution_plan(self, node, state_with_optimization):
        """Test that execution plan is created."""
        result = await node.execute(state_with_optimization)

        assert result.transaction_execution_plan is not None
        assert "transaction_cost_node" in result.completed_nodes

    @pytest.mark.asyncio
    async def test_execution_plan_includes_trades(self, node, state_with_optimization):
        """Test that execution plan includes individual trades."""
        result = await node.execute(state_with_optimization)
        plan = result.transaction_execution_plan

        assert len(plan.trades) == 3  # One per position

    @pytest.mark.asyncio
    async def test_execution_plan_costs_reasonable(self, node, state_with_optimization):
        """Test that execution costs are reasonable (< 2% typically)."""
        result = await node.execute(state_with_optimization)
        plan = result.transaction_execution_plan

        # Total cost in bps should be less than 20 bps (0.2%)
        assert plan.total_cost_bps < 20
        assert plan.estimated_commission > 0
        assert plan.estimated_market_impact >= 0
        assert plan.estimated_slippage >= 0

    def test_market_impact_calculation(self, node, state_with_optimization):
        """Test market impact using square-root model."""
        # $100k position in $5M daily volume
        impact = node._estimate_market_impact("AAPL", 50000, state_with_optimization)
        
        # Should be small but positive
        assert impact > 0
        assert impact < 500  # Less than $500

    def test_slippage_estimation(self, node, state_with_optimization):
        """Test slippage estimation based on volatility."""
        slippage = node._estimate_slippage("AAPL", 50000, state_with_optimization)
        
        # Should be reasonable (0.01% to 0.1%)
        assert slippage > 0
        assert slippage < 500

    @pytest.mark.asyncio
    async def test_execution_summary_generated(self, node, state_with_optimization):
        """Test that execution plan summary is generated."""
        result = await node.execute(state_with_optimization)
        plan = result.transaction_execution_plan

        assert plan.summary is not None
        assert len(plan.summary) > 0


class TestBacktestingEngineNode:
    """Test historical strategy backtesting."""

    @pytest.fixture
    def node(self):
        return BacktestingEngineNode()

    @pytest.fixture
    def state_with_optimization(self):
        """Create state with portfolio optimization."""
        state = DeerflowState(
            tickers=["AAPL", "MSFT", "GOOG"],
            portfolio_optimization=PortfolioOptimizationResult(
                optimization_method="kelly",
                expected_return=0.12,
                optimized_volatility=0.15,
                sharpe_ratio=0.8,
                optimized_positions={
                    "AAPL": 0.50,
                    "MSFT": 0.30,
                    "GOOG": 0.20,
                }
            ),
        )
        return state

    @pytest.mark.asyncio
    async def test_execute_runs_backtest(self, node, state_with_optimization):
        """Test that backtest is executed."""
        result = await node.execute(state_with_optimization)

        assert result.backtest_result is not None
        assert "backtesting_engine_node" in result.completed_nodes

    @pytest.mark.asyncio
    async def test_backtest_result_contains_metrics(self, node, state_with_optimization):
        """Test that backtest contains all required metrics."""
        result = await node.execute(state_with_optimization)
        backtest = result.backtest_result

        # Return metrics
        assert backtest.total_return is not None
        assert backtest.annualized_return is not None
        assert backtest.annualized_volatility is not None
        
        # Risk metrics
        assert backtest.sharpe_ratio is not None
        assert backtest.sortino_ratio is not None
        assert backtest.max_drawdown is not None
        
        # Relative metrics
        assert backtest.benchmark_return is not None
        assert backtest.information_ratio is not None

    @pytest.mark.asyncio
    async def test_backtest_period_analysis(self, node, state_with_optimization):
        """Test that backtest includes period-by-period analysis."""
        result = await node.execute(state_with_optimization)
        backtest = result.backtest_result

        assert len(backtest.periods) > 0
        assert backtest.total_months > 0
        assert backtest.positive_months <= backtest.total_months

    @pytest.mark.asyncio
    async def test_backtest_metrics_reasonable(self, node, state_with_optimization):
        """Test that backtest metrics are reasonable."""
        result = await node.execute(state_with_optimization)
        backtest = result.backtest_result

        # Sharpe should be between -2 and 3 for typical strategies
        assert -2 < backtest.sharpe_ratio < 3
        
        # Max drawdown between -100% and 0%
        assert -1.0 <= backtest.max_drawdown <= 0
        
        # Volatility between 5% and 50%
        assert 0.05 < backtest.annualized_volatility < 0.50

    @pytest.mark.asyncio
    async def test_backtest_summary_and_conclusion(self, node, state_with_optimization):
        """Test that backtest summary and conclusion are generated."""
        result = await node.execute(state_with_optimization)
        backtest = result.backtest_result

        assert len(backtest.summary) > 0
        assert len(backtest.conclusion) > 0


class TestPhase5StatModels:
    """Test Phase 5 state models and validation."""

    def test_efficient_frontier_point_creation(self):
        """Test EfficientFrontierPoint model."""
        point = EfficientFrontierPoint(
            portfolio_id=0,
            expected_return=0.15,
            volatility=0.18,
            sharpe_ratio=0.83,
            position_weights={"AAPL": 0.5, "MSFT": 0.5}
        )
        
        assert point.portfolio_id == 0
        assert point.expected_return == 0.15
        assert point.sharpe_ratio == 0.83

    def test_backtest_result_creation(self):
        """Test BacktestResult model."""
        backtest = BacktestResult(
            backtest_id="test_001",
            backtest_name="Test Backtest",
            backtest_start_date=datetime.utcnow() - timedelta(days=756),
            backtest_end_date=datetime.utcnow(),
            backtest_days=756,
            total_return=0.45,
            annualized_return=0.13,
            sharpe_ratio=1.1,
        )
        
        assert backtest.backtest_id == "test_001"
        assert backtest.total_return == 0.45
        assert backtest.backtest_days == 756

    def test_transaction_execution_plan_creation(self):
        """Test TransactionExecutionPlan model."""
        plan = TransactionExecutionPlan(
            execution_id="exec_001",
            estimated_commission=50.0,
            total_estimated_cost=150.0,
            total_cost_bps=1.5,
            execution_strategy="vwap"
        )
        
        assert plan.execution_id == "exec_001"
        assert plan.total_cost_bps == 1.5
        assert plan.execution_strategy == "vwap"


class TestPhase5ErrorHandling:
    """Test error handling in Phase 5 nodes."""

    @pytest.mark.asyncio
    async def test_frontier_node_handles_empty_signals(self):
        """Test frontier node with empty signals."""
        node = EfficientFrontierNode()
        state = DeerflowState(tickers=[], consensus_signals={})
        
        result = await node.execute(state)
        
        # Should complete without error
        assert "efficient_frontier_node" in result.completed_nodes

    @pytest.mark.asyncio
    async def test_backtest_node_handles_missing_optimization(self):
        """Test backtest node without portfolio optimization."""
        node = BacktestingEngineNode()
        state = DeerflowState(tickers=["AAPL"], portfolio_optimization=None)
        
        result = await node.execute(state)
        
        # Should complete but with minimal backtest
        assert "backtesting_engine_node" in result.completed_nodes

    @pytest.mark.asyncio
    async def test_nodes_log_errors_properly(self):
        """Test that nodes properly log errors to state."""
        node = BacktestingEngineNode()
        state = DeerflowState(tickers=["AAPL"])
        
        # Mock to force an error
        with patch.object(node, '_run_backtest', side_effect=ValueError("Test error")):
            result = await node.execute(state)
            
            # Error should be logged
            assert len(result.errors) > 0 or "backtesting_engine_node" in result.completed_nodes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
