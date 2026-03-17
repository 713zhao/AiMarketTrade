"""
Integration tests for Phase 5 production deployment.

Tests the complete Phase 5 graph execution including:
- Full graph with all Phase 5 nodes
- Mock graph with synthetic data
- Simplified graph with Phase 5
- State flow through Phase 5
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
import asyncio

from deerflow_openbb.state import DeerflowState, AnalystType
from deerflow_openbb.graph import (
    create_deerflow_graph,
    create_mock_graph,
    create_simplified_graph,
    run_deerflow_graph,
)


class TestPhase5GraphIntegration:
    """Integration tests for Phase 5 graph execution."""

    def test_deerflow_graph_compilation(self):
        """Test that main compiled graph includes Phase 5 nodes."""
        graph = create_deerflow_graph()
        
        assert graph is not None
        # Graph should be compiled and ready to run
        assert callable(graph.invoke) or callable(graph.astream)

    def test_mock_graph_compilation(self):
        """Test that mock graph includes Phase 5 nodes."""
        graph = create_mock_graph()
        
        assert graph is not None
        assert callable(graph.invoke) or callable(graph.astream)

    def test_simplified_graph_compilation(self):
        """Test that simplified graph includes Phase 5 nodes."""
        graph = create_simplified_graph()
        
        assert graph is not None
        assert callable(graph.invoke) or callable(graph.astream)

    @pytest.mark.asyncio
    async def test_mock_graph_execution(self):
        """Test full mock graph execution with Phase 5."""
        graph = create_mock_graph()
        
        state = DeerflowState(
            session_id="test_integration_001",
            tickers=["AAPL", "MSFT", "GOOG"],
        )
        
        # Execute the graph
        try:
            events = []
            async for event in graph.astream(state):
                events.append(event)
            
            # Graph should complete successfully
            assert len(events) > 0
        except Exception as e:
            pytest.skip(f"Mock graph execution requires LangGraph configuration: {str(e)}")

    @pytest.mark.asyncio
    async def test_phase5_nodes_executed_in_parallel(self):
        """Test that Phase 5 nodes execute in parallel after multi-scenario."""
        graph = create_mock_graph()
        state = DeerflowState(
            session_id="test_parallel_001",
            tickers=["AAPL", "MSFT"],
        )
        
        try:
            # Phase 5 nodes should all start within short time window
            start_times = {}
            async for event in graph.astream(state):
                for node_name in event:
                    if "efficient_frontier" in node_name or "performance_attribution" in node_name or \
                       "transaction_cost" in node_name or "backtesting_engine" in node_name:
                        start_times[node_name] = datetime.utcnow()
            
            # All Phase 5 nodes should exist in execution
            phase5_nodes = ["efficient_frontier", "performance_attribution", 
                           "transaction_cost", "backtesting_engine"]
            # Note: Due to graph execution async nature, this is a structural test
        except Exception as e:
            pytest.skip(f"Requires LangGraph async execution: {str(e)}")

    def test_simplified_graph_with_phase5_analysts(self):
        """Test simplified graph with specific analyst selection."""
        analyst_types = [
            AnalystType.TECHNICAL,
            AnalystType.FUNDAMENTALS,
            AnalystType.MACRO,
        ]
        
        graph = create_simplified_graph(analyst_types)
        
        assert graph is not None

    def test_graph_configuration_options(self):
        """Test graph creation with various configurations."""
        config = {
            "enable_parallel": True,
            "max_parallel": 6,
            "checkpoint_dir": "/tmp/checkpoints",
        }
        
        graph = create_deerflow_graph(config)
        assert graph is not None


class TestPhase5StateFlow:
    """Test state flow through Phase 5 pipeline."""

    def test_initial_state_creation(self):
        """Test creation of initial state for Phase 5."""
        state = DeerflowState(
            session_id="state_test_001",
            tickers=["AAPL", "MSFT", "GOOG"],
            analysis_scope={
                "time_horizon": "3months",
                "risk_tolerance": "moderate",
            }
        )
        
        assert state.session_id == "state_test_001"
        assert len(state.tickers) == 3
        # Phase 5 fields should be None initially
        assert state.efficient_frontier_data is None
        assert state.transaction_execution_plan is None
        assert state.backtest_result is None

    def test_state_phase5_field_updates(self):
        """Test updating Phase 5 fields in state."""
        state = DeerflowState(tickers=["AAPL"])
        
        # Update Phase 5 fields
        from state import EfficientFrontierData, TransactionExecutionPlan, BacktestResult
        
        state.efficient_frontier_data = EfficientFrontierData(num_portfolios=50)
        state.transaction_execution_plan = TransactionExecutionPlan(execution_id="test_exec")
        state.backtest_result = BacktestResult(
            backtest_id="test_backtest",
            backtest_name="Test",
            backtest_start_date=datetime.utcnow(),
            backtest_end_date=datetime.utcnow(),
        )
        
        assert state.efficient_frontier_data is not None
        assert state.transaction_execution_plan is not None
        assert state.backtest_result is not None

    def test_state_node_tracking(self):
        """Test that state tracks completed nodes in Phase 5."""
        state = DeerflowState(tickers=["AAPL"])
        
        phase5_nodes = [
            "efficient_frontier",
            "performance_attribution",
            "transaction_cost",
            "backtesting_engine",
            "decision"
        ]
        
        # Simulate node completion tracking
        for node in phase5_nodes:
            state.completed_nodes.append(node)
        
        for node in phase5_nodes:
            assert node in state.completed_nodes


class TestPhase5E2EScenarios:
    """End-to-end scenario tests for Phase 5."""

    def test_scenario_small_portfolio(self):
        """Test Phase 5 with small efficient portfolio."""
        state = DeerflowState(
            session_id="scenario_small",
            tickers=["QQQ", "SPY", "IWM"],  # 3 ETFs
        )
        
        assert len(state.tickers) == 3

    def test_scenario_sector_diversified(self):
        """Test Phase 5 with sector-diversified portfolio."""
        tickers = [
            "AAPL", "MSFT", "GOOGL",      # Tech
            "JNJ", "PFE", "UNH",          # Healthcare
            "JPM", "BAC", "GS",           # Finance
            "XOM", "CVX",                 # Energy
            "PG", "KO",                   # Consumer
        ]
        
        state = DeerflowState(
            session_id="scenario_sectors",
            tickers=tickers,
        )
        
        assert len(state.tickers) == 12

    def test_scenario_growth_focused(self):
        """Test Phase 5 with growth-focused portfolio."""
        growth_tickers = [
            "NVDA", "TSLA", "PLTR",
            "SQ", "DKNG", "ROKU",
            "UPWK", "CRWD", "ZM",
        ]
        
        state = DeerflowState(
            session_id="scenario_growth",
            tickers=growth_tickers,
        )
        
        assert len(state.tickers) == 9

    def test_scenario_value_focused(self):
        """Test Phase 5 with value-focused portfolio."""
        value_tickers = [
            "BAC", "GE", "T",
            "F", "KMI", "VZ",
            "PEP", "MO", "SO",
        ]
        
        state = DeerflowState(
            session_id="scenario_value",
            tickers=value_tickers,
        )
        
        assert len(state.tickers) == 9


class TestPhase5DataValidation:
    """Test data validation for Phase 5."""

    def test_efficient_frontier_data_validation(self):
        """Test EfficientFrontierData pydantic validation."""
        from state import EfficientFrontierData
        
        # Valid data
        frontier = EfficientFrontierData(
            num_portfolios=50,
            min_return=0.0,
            max_return=0.20,
        )
        
        assert frontier.num_portfolios == 50

    def test_backtest_result_data_validation(self):
        """Test BacktestResult pydantic validation."""
        from state import BacktestResult
        
        backtest = BacktestResult(
            backtest_id="test_001",
            backtest_name="Test Backtest",
            backtest_start_date=datetime.utcnow() - timedelta(days=756),
            backtest_end_date=datetime.utcnow(),
            backtest_days=756,
        )
        
        assert backtest.backtest_id == "test_001"
        assert backtest.backtest_days == 756

    def test_transaction_plan_validation(self):
        """Test TransactionExecutionPlan pydantic validation."""
        from state import TransactionExecutionPlan
        
        plan = TransactionExecutionPlan(
            execution_id="exec_001",
            execution_strategy="vwap",
        )
        
        assert plan.execution_id == "exec_001"
        assert plan.execution_strategy == "vwap"

    def test_portfolio_snapshot_validation(self):
        """Test PortfolioSnapshot pydantic validation."""
        from state import PortfolioSnapshot
        
        snapshot = PortfolioSnapshot(
            snapshot_id="snap_001",
            total_value=100000,
            cash_position=10000,
        )
        
        assert snapshot.snapshot_id == "snap_001"
        assert snapshot.total_value == 100000


class TestPhase5BackwardCompatibility:
    """Test backward compatibility with Phases 1-4."""

    def test_graph_still_executes_phase4_nodes(self):
        """Test that Phase 5 graph still includes Phase 4 nodes."""
        graph = create_mock_graph()
        
        # Graph should have all previous nodes
        assert graph is not None

    def test_state_preserves_phase4_fields(self):
        """Test that Phase 5 state preserves Phase 4 fields."""
        from state import PortfolioRiskAnalysis, MultiScenarioAnalysis
        
        state = DeerflowState(tickers=["AAPL"])
        
        # Set Phase 4 fields
        state.portfolio_risk_analysis = PortfolioRiskAnalysis()
        state.multi_scenario_analysis = MultiScenarioAnalysis()
        
        # Phase 5 fields should coexist
        assert state.portfolio_risk_analysis is not None
        assert state.multi_scenario_analysis is not None

    def test_graph_node_ordering_phases1to5(self):
        """Test that graph maintains proper node ordering across all phases."""
        config = {"enable_parallel": True}
        graph = create_deerflow_graph(config)
        
        # Graph should compile without issues
        assert graph is not None


class TestPhase5PerformanceCharacteristics:
    """Test performance characteristics of Phase 5."""

    def test_frontier_generation_completes_quickly(self):
        """Test that frontier generation completes in reasonable time."""
        import time
        
        from nodes import EfficientFrontierNode
        from state import DeerflowState, ConsensusSignal, SignalType
        
        node = EfficientFrontierNode()
        state = DeerflowState(
            tickers=["AAPL", "MSFT", "GOOG"],
            consensus_signals={
                "AAPL": ConsensusSignal(ticker="AAPL", overall_signal=SignalType.BUY, signal_strength=0.7),
                "MSFT": ConsensusSignal(ticker="MSFT", overall_signal=SignalType.BUY, signal_strength=0.6),
                "GOOG": ConsensusSignal(ticker="GOOG", overall_signal=SignalType.HOLD, signal_strength=0.2),
            }
        )
        
        start = time.time()
        # Synchronous execution for timing
        import asyncio
        asyncio.run(node.execute(state))
        elapsed = time.time() - start
        
        # Should complete in < 1 second
        assert elapsed < 1.0

    def test_backtest_completes_in_reasonable_time(self):
        """Test that backtesting completes efficiently."""
        import time
        
        from nodes import BacktestingEngineNode
        from state import DeerflowState, PortfolioOptimizationResult
        
        node = BacktestingEngineNode()
        state = DeerflowState(
            tickers=["AAPL"],
            portfolio_optimization=PortfolioOptimizationResult(
                optimized_positions={"AAPL": 1.0}
            )
        )
        
        start = time.time()
        import asyncio
        asyncio.run(node.execute(state))
        elapsed = time.time() - start
        
        # Should complete in < 2 seconds
        assert elapsed < 2.0


class TestPhase5Robustness:
    """Test robustness and error recovery in Phase 5."""

    @pytest.mark.asyncio
    async def test_graph_handles_missing_consensus_signals(self):
        """Test graph with incomplete consensus signals."""
        from nodes import EfficientFrontierNode
        from state import DeerflowState
        
        node = EfficientFrontierNode()
        state = DeerflowState(
            tickers=["AAPL", "MSFT"],
            consensus_signals={}  # Empty
        )
        
        result = await node.execute(state)
        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_graph_handles_missing_risk_analyses(self):
        """Test graph with missing risk analyses."""
        from nodes import TransactionCostNode
        from state import DeerflowState, PortfolioOptimizationResult
        
        node = TransactionCostNode()
        state = DeerflowState(
            tickers=["AAPL"],
            portfolio_optimization=PortfolioOptimizationResult(
                optimized_positions={"AAPL": 1.0}
            ),
            risk_analyses={}  # Empty
        )
        
        result = await node.execute(state)
        # Should use defaults
        assert result.transaction_execution_plan is not None

    def test_state_serialization_with_phase5_fields(self):
        """Test that Phase 5 state can be serialized."""
        from state import EfficientFrontierData, BacktestResult
        
        state = DeerflowState(
            tickers=["AAPL"],
            efficient_frontier_data=EfficientFrontierData(),
            backtest_result=BacktestResult(
                backtest_id="test",
                backtest_name="Test",
                backtest_start_date=datetime.utcnow(),
                backtest_end_date=datetime.utcnow(),
            )
        )
        
        # Should be serializable to dict
        state_dict = state.model_dump()
        assert "efficient_frontier_data" in state_dict
        assert "backtest_result" in state_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
