"""
Comprehensive validation tests for Phase 5 state models.

Tests model creation, validation, edge cases, and serialization.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from state import (
    BacktestPeriod,
    BacktestResult,
    EfficientFrontierData,
    EfficientFrontierPoint,
    TransactionExecutionPlan,
    PortfolioSnapshot,
    LiveTradingSession,
    PerformanceMetricsSnapshot,
)


class TestBacktestPeriod:
    """Tests for BacktestPeriod model."""

    def test_creation_with_required_fields(self):
        """Test creating BacktestPeriod with required fields."""
        period = BacktestPeriod(
            period_id=1,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 2, 1),
        )
        
        assert period.period_id == 1
        assert period.portfolio_return == 0.0  # Default

    def test_creation_with_all_fields(self):
        """Test creating BacktestPeriod with all fields."""
        period = BacktestPeriod(
            period_id=1,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 2, 1),
            portfolio_return=0.05,
            benchmark_return=0.03,
            outperformance=0.02,
            volatility=0.15,
            max_drawdown=-0.10,
            sharpe_ratio=0.33,
            num_trades=12,
            total_costs=500.0,
            turnover=0.30,
        )
        
        assert period.portfolio_return == 0.05
        assert period.sharpe_ratio == 0.33
        assert period.num_trades == 12

    def test_period_date_ordering(self):
        """Test that period dates are in correct order."""
        start = datetime(2023, 1, 1)
        end = datetime(2023, 2, 1)
        
        period = BacktestPeriod(
            period_id=1,
            start_date=start,
            end_date=end,
        )
        
        assert period.start_date < period.end_date

    def test_period_serialization(self):
        """Test BacktestPeriod serialization."""
        period = BacktestPeriod(
            period_id=1,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 2, 1),
            portfolio_return=0.05,
            sharpe_ratio=0.33,
        )
        
        period_dict = period.model_dump()
        
        assert period_dict["period_id"] == 1
        assert period_dict["portfolio_return"] == 0.05


class TestBacktestResult:
    """Tests for BacktestResult model."""

    def test_minimal_creation(self):
        """Test creating BacktestResult with minimal fields."""
        backtest = BacktestResult(
            backtest_id="test_001",
            backtest_name="Test Strategy",
            backtest_start_date=datetime(2023, 1, 1),
            backtest_end_date=datetime(2025, 12, 31),
            backtest_days=756,
        )
        
        assert backtest.backtest_id == "test_001"
        assert backtest.backtest_days == 756

    def test_complete_backtest_creation(self):
        """Test creating complete BacktestResult."""
        start = datetime(2023, 1, 1)
        end = datetime(2025, 12, 31)
        
        backtest = BacktestResult(
            backtest_id="test_001",
            backtest_name="Full Strategy Test",
            backtest_start_date=start,
            backtest_end_date=end,
            backtest_days=756,
            starting_portfolio={"AAPL": 1000, "MSFT": 1000},
            ending_portfolio={"AAPL": 1500, "MSFT": 1200},
            rebalance_frequency="monthly",
            total_return=0.45,
            annualized_return=0.13,
            annualized_volatility=0.12,
            sharpe_ratio=1.08,
            sortino_ratio=1.5,
            benchmark_return=0.10,
            benchmark_volatility=0.10,
            outperformance=0.03,
            tracking_error=0.05,
            information_ratio=0.6,
            max_drawdown=-0.18,
            total_trades=120,
            total_costs=2500.0,
            positive_months=24,
            total_months=36,
        )
        
        assert backtest.total_return == 0.45
        assert backtest.sharpe_ratio == 1.08
        assert backtest.positive_months == 24

    def test_backtest_with_periods(self):
        """Test BacktestResult with period-by-period data."""
        periods = [
            BacktestPeriod(
                period_id=i,
                start_date=datetime(2023, 1, 1) + timedelta(days=i*30),
                end_date=datetime(2023, 1, 1) + timedelta(days=(i+1)*30),
                portfolio_return=0.02 + (i * 0.001),
                sharpe_ratio=0.5 + (i * 0.05),
            )
            for i in range(12)
        ]
        
        backtest = BacktestResult(
            backtest_id="test_periods",
            backtest_name="With Periods",
            backtest_start_date=datetime(2023, 1, 1),
            backtest_end_date=datetime(2024, 1, 1),
            backtest_days=252,
            periods=periods,
        )
        
        assert len(backtest.periods) == 12

    def test_backtest_metrics_validation(self):
        """Test that backtest metrics are within reasonable ranges."""
        backtest = BacktestResult(
            backtest_id="valid_test",
            backtest_name="Valid Test",
            backtest_start_date=datetime(2023, 1, 1),
            backtest_end_date=datetime(2025, 12, 31),
            backtest_days=756,
            sharpe_ratio=2.5,
            max_drawdown=-0.25,
            annualized_volatility=0.15,
        )
        
        # Sharpe reasonable for good strategy
        assert 0 < backtest.sharpe_ratio < 5
        
        # Max drawdown reasonable
        assert -1.0 <= backtest.max_drawdown <= 0
        
        # Volatility reasonable
        assert 0 < backtest.annualized_volatility < 1.0

    def test_backtest_serialization(self):
        """Test BacktestResult serialization."""
        backtest = BacktestResult(
            backtest_id="test_001",
            backtest_name="Serialization Test",
            backtest_start_date=datetime(2023, 1, 1),
            backtest_end_date=datetime(2025, 12, 31),
            backtest_days=756,
            total_return=0.45,
        )
        
        backtest_dict = backtest.model_dump()
        
        assert backtest_dict["backtest_id"] == "test_001"
        assert backtest_dict["total_return"] == 0.45


class TestEfficientFrontierPoint:
    """Tests for EfficientFrontierPoint model."""

    def test_frontier_point_creation(self):
        """Test creating EfficientFrontierPoint."""
        point = EfficientFrontierPoint(
            portfolio_id=0,
            expected_return=0.10,
            volatility=0.12,
            sharpe_ratio=0.83,
            position_weights={"AAPL": 0.5, "MSFT": 0.5},
        )
        
        assert point.portfolio_id == 0
        assert point.expected_return == 0.10
        assert point.sharpe_ratio == 0.83

    def test_frontier_point_with_risk_metrics(self):
        """Test frontier point with comprehensive risk metrics."""
        point = EfficientFrontierPoint(
            portfolio_id=25,
            expected_return=0.15,
            volatility=0.18,
            sharpe_ratio=0.83,
            position_weights={
                "AAPL": 0.30,
                "MSFT": 0.25,
                "GOOG": 0.20,
                "NVDA": 0.25,
            },
            var_95=-0.03,
            max_drawdown=-0.20,
            diversification_ratio=1.2,
            concentration_hhi=0.25,
        )
        
        assert len(point.position_weights) == 4
        assert point.diversification_ratio == 1.2

    def test_frontier_point_regime_returns(self):
        """Test frontier point with regime-specific returns."""
        point = EfficientFrontierPoint(
            portfolio_id=10,
            expected_return=0.12,
            volatility=0.14,
            sharpe_ratio=0.86,
            position_weights={"AAPL": 0.7, "MSFT": 0.3},
            returns_by_regime={
                "bull_high_vol": 0.18,
                "bull_low_vol": 0.14,
                "bear_high_vol": -0.05,
                "bear_low_vol": 0.02,
            },
        )
        
        assert len(point.returns_by_regime) == 4
        assert point.returns_by_regime["bull_high_vol"] == 0.18


class TestEfficientFrontierData:
    """Tests for EfficientFrontierData model."""

    def test_frontier_data_creation(self):
        """Test creating EfficientFrontierData."""
        frontier = EfficientFrontierData(
            num_portfolios=50,
            min_return=0.0,
            max_return=0.20,
        )
        
        assert frontier.num_portfolios == 50

    def test_frontier_with_portfolios(self):
        """Test frontier with multiple portfolios."""
        portfolios = [
            EfficientFrontierPoint(
                portfolio_id=i,
                expected_return=i * 0.004,  # 0% to 20%
                volatility=0.05 + (i * 0.003),  # Increasing vol
                sharpe_ratio=0.7 + (i * 0.01),
                position_weights={"AAPL": 0.5, "MSFT": 0.5},
            )
            for i in range(50)
        ]
        
        frontier = EfficientFrontierData(
            num_portfolios=50,
            min_return=0.0,
            max_return=0.20,
            portfolios=portfolios,
        )
        
        assert len(frontier.portfolios) == 50

    def test_frontier_special_portfolios(self):
        """Test frontier with special portfolio designations."""
        min_var = EfficientFrontierPoint(
            portfolio_id=0,
            expected_return=0.05,
            volatility=0.08,
            sharpe_ratio=0.625,
            position_weights={"AAPL": 0.4, "MSFT": 0.6},
        )
        
        max_sharpe = EfficientFrontierPoint(
            portfolio_id=25,
            expected_return=0.12,
            volatility=0.14,
            sharpe_ratio=0.86,
            position_weights={"AAPL": 0.35, "MSFT": 0.25, "GOOG": 0.40},
        )
        
        frontier = EfficientFrontierData(
            num_portfolios=50,
            global_minimum_variance=min_var,
            maximum_sharpe_portfolio=max_sharpe,
        )
        
        assert frontier.global_minimum_variance.sharpe_ratio < frontier.maximum_sharpe_portfolio.sharpe_ratio

    def test_frontier_constraint_impacts(self):
        """Test frontier constraint impact analysis."""
        frontier = EfficientFrontierData(
            num_portfolios=50,
            constraints_active=["position_limit_30_pct", "sector_limit"],
            constraint_impacts={
                "position_limit_30_pct": -0.02,  # 2% performance cost
                "sector_limit": -0.01,  # 1% performance cost
            },
        )
        
        assert len(frontier.constraints_active) == 2
        assert frontier.constraint_impacts["position_limit_30_pct"] == -0.02


class TestTransactionExecutionPlan:
    """Tests for TransactionExecutionPlan model."""

    def test_execution_plan_creation(self):
        """Test creating TransactionExecutionPlan."""
        plan = TransactionExecutionPlan(
            execution_id="exec_001",
            execution_date=datetime.utcnow(),
        )
        
        assert plan.execution_id == "exec_001"

    def test_execution_plan_with_costs(self):
        """Test execution plan with cost breakdown."""
        plan = TransactionExecutionPlan(
            execution_id="exec_001",
            estimated_commission=50.0,
            estimated_market_impact=75.0,
            estimated_slippage=30.0,
            estimated_opportunity_cost=10.0,
            total_estimated_cost=165.0,
            total_cost_bps=1.65,
        )
        
        assert plan.total_estimated_cost == 165.0
        assert plan.total_cost_bps == 1.65

    def test_execution_plan_strategies(self):
        """Test different execution strategies."""
        strategies = ["vwap", "twap", "direct", "adaptive"]
        
        for strategy in strategies:
            plan = TransactionExecutionPlan(
                execution_id=f"exec_{strategy}",
                execution_strategy=strategy,
            )
            
            assert plan.execution_strategy == strategy

    def test_execution_plan_constraints(self):
        """Test execution plan with constraints."""
        plan = TransactionExecutionPlan(
            execution_id="exec_constrained",
            max_order_size=0.1,  # 10% of daily volume
            avoid_news=True,
            tax_aware=True,
            market_hours_only=True,
        )
        
        assert plan.max_order_size == 0.1
        assert plan.avoid_news is True
        assert plan.tax_aware is True

    def test_execution_plan_trades(self):
        """Test execution plan with individual trades."""
        trades = [
            {"ticker": "AAPL", "action": "BUY", "size": 100},
            {"ticker": "MSFT", "action": "SELL", "size": 50},
        ]
        
        plan = TransactionExecutionPlan(
            execution_id="exec_trades",
            trades=trades,
        )
        
        assert len(plan.trades) == 2


class TestPortfolioSnapshot:
    """Tests for PortfolioSnapshot model."""

    def test_snapshot_creation(self):
        """Test creating PortfolioSnapshot."""
        snapshot = PortfolioSnapshot(
            snapshot_id="snap_001",
            total_value=100000,
        )
        
        assert snapshot.snapshot_id == "snap_001"
        assert snapshot.total_value == 100000

    def test_snapshot_with_positions(self):
        """Test snapshot with holdings."""
        snapshot = PortfolioSnapshot(
            snapshot_id="snap_001",
            total_value=100000,
            current_positions={
                "AAPL": 0.40,
                "MSFT": 0.35,
                "GOOG": 0.25,
            },
            target_positions={
                "AAPL": 0.40,
                "MSFT": 0.35,
                "GOOG": 0.25,
            },
            position_values={
                "AAPL": 40000,
                "MSFT": 35000,
                "GOOG": 25000,
            },
        )
        
        assert len(snapshot.current_positions) == 3

    def test_snapshot_with_drift(self):
        """Test snapshot with position drift."""
        snapshot = PortfolioSnapshot(
            snapshot_id="snap_drift",
            total_value=100000,
            current_positions={"AAPL": 0.45, "MSFT": 0.30, "GOOG": 0.25},
            target_positions={"AAPL": 0.40, "MSFT": 0.35, "GOOG": 0.25},
            position_drift={"AAPL": 0.05, "MSFT": -0.05, "GOOG": 0.0},
        )
        
        assert snapshot.position_drift["AAPL"] == 0.05

    def test_snapshot_alert_flags(self):
        """Test snapshot with alert flags."""
        snapshot = PortfolioSnapshot(
            snapshot_id="snap_alerts",
            total_value=100000,
            rebalancing_needed=True,
            risk_threshold_exceeded=False,
            cash_needed=False,
        )
        
        assert snapshot.rebalancing_needed is True


class TestLiveTradingSession:
    """Tests for LiveTradingSession model."""

    def test_session_creation(self):
        """Test creating LiveTradingSession."""
        session = LiveTradingSession(
            session_id="session_001",
            session_start=datetime.utcnow(),
        )
        
        assert session.session_id == "session_001"
        assert session.is_active is True

    def test_session_with_trades(self):
        """Test session with executed trades."""
        session = LiveTradingSession(
            session_id="session_001",
            session_start=datetime.utcnow(),
            starting_value=100000,
            current_value=101500,
            session_pnl=1500,
            session_pnl_pct=0.015,
            trades_executed=[
                {"ticker": "AAPL", "action": "BUY", "qty": 10, "price": 150},
                {"ticker": "MSFT", "action": "SELL", "qty": 5, "price": 300},
            ],
        )
        
        assert session.current_value == 101500
        assert len(session.trades_executed) == 2

    def test_session_execution_metrics(self):
        """Test session with execution metrics."""
        session = LiveTradingSession(
            session_id="session_metrics",
            session_start=datetime.utcnow(),
            total_commissions=50.0,
            total_slippage=25.0,
            total_market_impact=15.0,
        )
        
        assert session.total_commissions == 50.0


class TestPerformanceMetricsSnapshot:
    """Tests for PerformanceMetricsSnapshot model."""

    def test_metrics_creation(self):
        """Test creating PerformanceMetricsSnapshot."""
        metrics = PerformanceMetricsSnapshot()
        
        assert metrics.daily_return == 0.0  # Default

    def test_metrics_with_returns(self):
        """Test metrics with return data."""
        metrics = PerformanceMetricsSnapshot(
            daily_return=0.002,
            weekly_return=0.015,
            monthly_return=0.045,
            ytd_return=0.35,
            inception_return=0.85,
        )
        
        assert metrics.inception_return > metrics.ytd_return
        assert metrics.ytd_return > metrics.monthly_return

    def test_metrics_with_volatility(self):
        """Test metrics with volatility data."""
        metrics = PerformanceMetricsSnapshot(
            daily_volatility=0.01,
            rolling_volatility_20d=0.12,
            rolling_volatility_60d=0.11,
        )
        
        assert metrics.rolling_volatility_60d > metrics.rolling_volatility_20d

    def test_metrics_risk_adjusted(self):
        """Test risk-adjusted metrics."""
        metrics = PerformanceMetricsSnapshot(
            sharpe_ratio_annual=1.1,
            sortino_ratio=1.5,
            calmar_ratio=0.8,
            current_drawdown=-0.08,
        )
        
        assert metrics.sharpe_ratio_annual > 0
        assert metrics.sortino_ratio > metrics.sharpe_ratio_annual

    def test_metrics_win_rate(self):
        """Test win rate calculation."""
        metrics = PerformanceMetricsSnapshot(
            positive_days=60,
            total_days=100,
            win_rate=0.60,
        )
        
        assert metrics.win_rate == 0.60


class TestPhase5StateIntegration:
    """Test integration of Phase 5 models with DeerflowState."""

    def test_state_with_all_phase5_models(self):
        """Test DeerflowState with all Phase 5 models."""
        from state import DeerflowState
        
        state = DeerflowState(
            tickers=["AAPL", "MSFT"],
            efficient_frontier_data=EfficientFrontierData(),
            transaction_execution_plan=TransactionExecutionPlan(execution_id="test"),
            backtest_result=BacktestResult(
                backtest_id="test",
                backtest_name="Test",
                backtest_start_date=datetime.utcnow(),
                backtest_end_date=datetime.utcnow(),
            ),
        )
        
        assert state.efficient_frontier_data is not None
        assert state.transaction_execution_plan is not None
        assert state.backtest_result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
