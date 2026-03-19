"""
Phase 7: Advanced Strategies & Derivatives Trading - Unit Tests

Tests for options, futures, crypto derivatives, Greeks management,
hedging strategies, volatility arbitrage, and pair trading.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
import math

from src.models import (
    OptionContract,
    FuturesContract,
    CryptoDerivative,
    MultiLegOrder,
    GreeksSnapshot,
    HedgeAllocation,
    StrategyPerformance,
    VolatilityProfile,
    PairCorrelation,
    DeerflowState,
)
from src.nodes.advanced_nodes import (
    GreeksCalculator,
    StrategyBuilder,
    OptionsAnalysisNode,
    FuturesAnalysisNode,
    CryptoDerivativesNode,
    StrategyBuilderNode,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_option_contract() -> OptionContract:
    """Create a sample options contract for testing."""
    return OptionContract(
        contract_id="AAPL_CALL_150_30DTE",
        ticker="AAPL",
        contract_type="CALL",
        expiration=datetime.utcnow() + timedelta(days=30),
        strike=150.0,
        bid=2.50,
        ask=2.60,
        last=2.55,
        volume=5000,
        open_interest=25000,
        implied_volatility=0.25,
        delta=0.65,
        gamma=0.05,
        theta=-0.15,
        vega=0.20,
        rho=0.08,
        is_tradeable=True,
    )


@pytest.fixture
def sample_futures_contract() -> FuturesContract:
    """Create a sample futures contract for testing."""
    return FuturesContract(
        contract_id="ES_MAR_2026",
        symbol="ES",
        contract_code="ESH26",
        expiration=datetime(2026, 3, 20),
        multiplier=50.0,
        bid=5050.0,
        ask=5050.25,
        current_price=5050.125,
        settlement_price=5045.0,
        daily_change=5.125,
        daily_change_pct=0.10,
        volume=1000000,
        open_interest=2500000,
        bid_volume=10000,
        ask_volume=10000,
        contract_type="INDEX",
        exchange="CME",
    )


@pytest.fixture
def sample_crypto_derivative() -> CryptoDerivative:
    """Create a sample crypto derivative for testing."""
    return CryptoDerivative(
        contract_id="BTC_PERP_BINANCE",
        underlying="BTC",
        contract_type="PERPETUAL",
        expiration=None,
        bid=42000.0,
        ask=42005.0,
        index_price=42002.0,
        mark_price=42002.5,
        funding_rate=0.0001,
        funding_rate_8h=0.00015,
        bid_volume=100.0,
        ask_volume=100.0,
        volume_24h=10000000.0,
        open_interest=50000.0,
        liquidation_price_long=40000.0,
        liquidation_price_short=44000.0,
        exchange="Binance",
    )


@pytest.fixture
def sample_deerflow_state() -> DeerflowState:
    """Create a sample DeerflowState for testing."""
    return DeerflowState(
        session_id="test_session_phase7",
        tickers=["AAPL", "SPY", "QQQ"],
        target_delta=0.0,
        rebalance_threshold=0.15,
    )


# ============================================================================
# GREEKS CALCULATOR TESTS
# ============================================================================

class TestGreeksCalculator:
    """Test Greeks calculation using Black-Scholes model."""

    def test_black_scholes_call_atm(self):
        """Test Black-Scholes calculation for ATM call option."""
        greeks = GreeksCalculator.black_scholes(
            spot=100.0,
            strike=100.0,
            time_to_expiration=0.25,
            risk_free_rate=0.05,
            volatility=0.20,
            option_type="CALL"
        )
        
        assert "delta" in greeks
        assert "gamma" in greeks
        assert "theta" in greeks
        assert "vega" in greeks
        assert "rho" in greeks
        
        # ATM call delta should be around 0.5
        assert 0.4 < greeks["delta"] < 0.6
        
        # Gamma should be positive
        assert greeks["gamma"] > 0
        
        # Theta should be negative for long call
        assert greeks["theta"] < 0
        
        # Vega should be positive
        assert greeks["vega"] > 0

    def test_black_scholes_put_otm(self):
        """Test Black-Scholes calculation for OTM put option."""
        greeks = GreeksCalculator.black_scholes(
            spot=100.0,
            strike=95.0,
            time_to_expiration=0.25,
            risk_free_rate=0.05,
            volatility=0.20,
            option_type="PUT"
        )
        
        # OTM put delta should be negative and close to 0
        assert -0.5 < greeks["delta"] < 0
        
        # Gamma should be positive
        assert greeks["gamma"] > 0

    def test_intrinsic_greeks_expired(self):
        """Test Greeks for expired option (intrinsic value only)."""
        greeks = GreeksCalculator._intrinsic_greeks(
            spot=105.0,
            strike=100.0,
            option_type="CALL"
        )
        
        # ITM call has delta = 1.0
        assert greeks["delta"] == 1.0
        assert greeks["gamma"] == 0.0
        assert greeks["theta"] == 0.0

    def test_aggregate_greeks(self):
        """Test aggregation of Greeks across positions."""
        positions = [
            {
                "ticker": "AAPL",
                "quantity": 100,
                "delta": 0.65,
                "gamma": 0.05,
                "theta": -0.15,
                "vega": 0.20,
                "rho": 0.08,
            },
            {
                "ticker": "AAPL",
                "quantity": -50,
                "delta": -0.65,
                "gamma": -0.05,
                "theta": 0.15,
                "vega": -0.20,
                "rho": -0.08,
            },
        ]
        
        aggregated = GreeksCalculator.aggregate_greeks(positions)
        
        # Check aggregation math
        assert aggregated["total_delta"] == 100 * 0.65 - 50 * 0.65
        assert aggregated["total_gamma"] == 100 * 0.05 - 50 * 0.05
        assert aggregated["total_theta"] == 100 * (-0.15) - 50 * 0.15
        assert aggregated["total_vega"] == 100 * 0.20 - 50 * 0.20
        assert aggregated["total_rho"] == 100 * 0.08 - 50 * 0.08


# ============================================================================
# STRATEGY BUILDER TESTS
# ============================================================================

class TestStrategyBuilder:
    """Test multi-leg strategy construction."""

    def test_strategy_templates_exist(self):
        """Test that all strategy templates are defined."""
        expected_strategies = [
            "call_spread",
            "put_spread",
            "straddle",
            "strangle",
            "iron_condor",
            "collar",
        ]
        
        for strategy in expected_strategies:
            assert strategy in StrategyBuilder.STRATEGIES
            assert "legs" in StrategyBuilder.STRATEGIES[strategy]
            assert "description" in StrategyBuilder.STRATEGIES[strategy]

    def test_build_call_spread(self):
        """Test building a bull call spread strategy."""
        strategy = StrategyBuilder.build_strategy(
            strategy_name="call_spread",
            ticker="AAPL",
            spot_price=150.0,
            quantity=1,
            expiration_days=30,
            implied_vol=0.25,
        )
        
        assert strategy["strategy_name"] == "call_spread"
        assert strategy["ticker"] == "AAPL"
        assert len(strategy["legs"]) == 2
        
        # First leg should be long call
        assert strategy["legs"][0]["action"] == "BUY"
        assert strategy["legs"][0]["type"] == "CALL"
        
        # Second leg should be short call
        assert strategy["legs"][1]["action"] == "SELL"
        assert strategy["legs"][1]["type"] == "CALL"

    def test_build_iron_condor(self):
        """Test building an iron condor strategy."""
        strategy = StrategyBuilder.build_strategy(
            strategy_name="iron_condor",
            ticker="SPY",
            spot_price=450.0,
            quantity=1,
            expiration_days=45,
            implied_vol=0.18,
        )
        
        assert strategy["strategy_name"] == "iron_condor"
        assert len(strategy["legs"]) == 4  # 4-leg strategy
        
        # Should have 2 calls and 2 puts
        calls = [leg for leg in strategy["legs"] if leg["type"] == "CALL"]
        puts = [leg for leg in strategy["legs"] if leg["type"] == "PUT"]
        
        assert len(calls) == 2
        assert len(puts) == 2


# ============================================================================
# STATE MODEL TESTS
# ============================================================================

class TestOptionContractModel:
    """Test OptionContract pydantic model."""

    def test_create_call_option(self, sample_option_contract):
        """Test creating a call option contract."""
        assert sample_option_contract.ticker == "AAPL"
        assert sample_option_contract.contract_type == "CALL"
        assert sample_option_contract.strike == 150.0
        assert sample_option_contract.delta == 0.65

    def test_delta_constraint(self):
        """Test that delta is constrained to [-1, 1]."""
        valid_contracts = [
            {"delta": 1.0},  # Max delta
            {"delta": -1.0},  # Min delta
            {"delta": 0.0},  # Zero delta
        ]
        
        for contract_data in valid_contracts:
            contract = OptionContract(
                contract_id="TEST",
                ticker="AAPL",
                contract_type="CALL",
                expiration=datetime.utcnow() + timedelta(days=30),
                strike=150.0,
                delta=contract_data["delta"],
            )
            assert contract.delta == contract_data["delta"]

    def test_delta_invalid_constraint(self):
        """Test that invalid delta raises validation error."""
        with pytest.raises(ValueError):
            OptionContract(
                contract_id="TEST",
                ticker="AAPL",
                contract_type="CALL",
                expiration=datetime.utcnow() + timedelta(days=30),
                strike=150.0,
                delta=1.5,  # Invalid: >1.0
            )


class TestFuturesContractModel:
    """Test FuturesContract pydantic model."""

    def test_create_futures(self, sample_futures_contract):
        """Test creating a futures contract."""
        assert sample_futures_contract.symbol == "ES"
        assert sample_futures_contract.contract_code == "ESH26"
        assert sample_futures_contract.multiplier == 50.0
        assert sample_futures_contract.contract_type == "INDEX"

    def test_multiplier_positive(self):
        """Test that multiplier must be positive."""
        with pytest.raises(ValueError):
            FuturesContract(
                contract_id="TEST",
                symbol="ES",
                contract_code="ESH26",
                expiration=datetime(2026, 3, 20),
                multiplier=-50.0,  # Invalid: negative
            )


class TestGreeksSnapshotModel:
    """Test GreeksSnapshot pydantic model."""

    def test_create_greeks_snapshot(self):
        """Test creating a Greeks snapshot."""
        snapshot = GreeksSnapshot(
            snapshot_id="SNAPSHOT_001",
            position_id="POS_001",
            total_delta=1.5,
            total_gamma=0.05,
            total_theta=-0.20,
            total_vega=0.15,
            total_rho=0.10,
        )
        
        assert snapshot.total_delta == 1.5
        assert snapshot.delta_drift_alert == False
        assert snapshot.rebalance_needed == False

    def test_greeks_alerts(self):
        """Test Greeks alert triggering."""
        snapshot = GreeksSnapshot(
            snapshot_id="SNAPSHOT_002",
            position_id="POS_002",
            total_delta=2.0,
            delta_drift_alert=True,
            gamma_risk_high=True,
            rebalance_needed=True,
        )
        
        assert snapshot.delta_drift_alert == True
        assert snapshot.gamma_risk_high == True
        assert snapshot.rebalance_needed == True


class TestStrategyPerformanceModel:
    """Test StrategyPerformance pydantic model."""

    def test_create_strategy_performance(self):
        """Test creating a strategy performance tracker."""
        perf = StrategyPerformance(
            performance_id="PERF_001",
            strategy_id="STRAT_001",
            strategy_name="call_spread",
            entry_price=100.0,
            entry_capital=5000.0,
            current_price=105.0,
            days_held=15,
        )
        
        assert perf.status == "ACTIVE"
        assert perf.days_held == 15

    def test_strategy_return_calculation(self):
        """Test that return calculations are tracked."""
        perf = StrategyPerformance(
            performance_id="PERF_002",
            strategy_id="STRAT_002",
            strategy_name="iron_condor",
            entry_price=100.0,
            entry_capital=10000.0,
            theoretical_pnl=500.0,
            return_pct=5.0,
        )
        
        assert perf.theoretical_pnl == 500.0
        assert perf.return_pct == 5.0


class TestVolatilityProfileModel:
    """Test VolatilityProfile pydantic model."""

    def test_create_volatility_profile(self):
        """Test creating a volatility profile."""
        vol_prof = VolatilityProfile(
            profile_id="VOL_001",
            ticker="AAPL",
            iv_30d=0.25,
            iv_60d=0.23,
            iv_90d=0.22,
            realized_vol_20d=0.20,
            realized_vol_60d=0.18,
            iv_percentile=75.0,
        )
        
        assert vol_prof.ticker == "AAPL"
        assert vol_prof.iv_percentile == 75.0
        assert 0 <= vol_prof.iv_percentile <= 100

    def test_iv_percentile_constraint(self):
        """Test that IV percentile is constrained to [0, 100]."""
        with pytest.raises(ValueError):
            VolatilityProfile(
                profile_id="VOL_002",
                ticker="SPY",
                iv_percentile=150.0,  # Invalid: >100
            )


class TestPairCorrelationModel:
    """Test PairCorrelation pydantic model."""

    def test_create_pair_correlation(self):
        """Test creating a pair correlation."""
        pair = PairCorrelation(
            pair_id="PAIR_001",
            ticker1="AAPL",
            ticker2="MSFT",
            correlation_60d=0.65,
            correlation_252d=0.60,
            current_spread=-2.5,
            mean_spread=0.0,
            std_spread=2.0,
            zscore_spread=-1.25,
        )
        
        assert pair.ticker1 == "AAPL"
        assert pair.ticker2 == "MSFT"
        # Correlation should be in [-1, 1]
        assert -1 <= pair.correlation_60d <= 1

    def test_pair_trading_signal(self):
        """Test pair trading signal generation."""
        pair = PairCorrelation(
            pair_id="PAIR_002",
            ticker1="GLD",
            ticker2="DBC",
            current_trade="LONG_1_SHORT_2",
            entry_date=datetime.utcnow() - timedelta(days=5),
            status="ACTIVE_TRADE",
        )
        
        assert pair.current_trade == "LONG_1_SHORT_2"
        assert pair.status == "ACTIVE_TRADE"


# ============================================================================
# PHASE 7 STATE EXTENSION TESTS
# ============================================================================

class TestPhase7StateExtension:
    """Test Phase 7 fields added to DeerflowState."""

    def test_phase7_fields_exist(self, sample_deerflow_state):
        """Test that all Phase 7 fields exist in state."""
        assert hasattr(sample_deerflow_state, "active_options")
        assert hasattr(sample_deerflow_state, "active_futures")
        assert hasattr(sample_deerflow_state, "active_crypto_derivatives")
        assert hasattr(sample_deerflow_state, "active_strategies")
        assert hasattr(sample_deerflow_state, "strategy_performance")
        assert hasattr(sample_deerflow_state, "current_greeks")
        assert hasattr(sample_deerflow_state, "greek_alerts")
        assert hasattr(sample_deerflow_state, "recommended_hedges")
        assert hasattr(sample_deerflow_state, "active_hedges")
        assert hasattr(sample_deerflow_state, "volatility_profiles")
        assert hasattr(sample_deerflow_state, "vol_opportunities")
        assert hasattr(sample_deerflow_state, "correlations")
        assert hasattr(sample_deerflow_state, "active_pairs")
        assert hasattr(sample_deerflow_state, "target_delta")
        assert hasattr(sample_deerflow_state, "rebalance_threshold")

    def test_derivatives_positions(self, sample_deerflow_state):
        """Test tracking options, futures, and crypto positions."""
        # Add sample positions
        sample_deerflow_state.active_options["AAPL_CALL_150"] = OptionContract(
            contract_id="AAPL_CALL_150",
            ticker="AAPL",
            contract_type="CALL",
            expiration=datetime.utcnow() + timedelta(days=30),
            strike=150.0,
        )
        
        assert "AAPL_CALL_150" in sample_deerflow_state.active_options
        assert len(sample_deerflow_state.active_options) == 1

    def test_greeks_management(self, sample_deerflow_state):
        """Test Greeks management fields."""
        sample_deerflow_state.target_delta = 0.0
        sample_deerflow_state.rebalance_threshold = 0.20
        
        assert sample_deerflow_state.target_delta == 0.0
        assert sample_deerflow_state.rebalance_threshold == 0.20
        
        # Verify constraints
        assert -1 <= sample_deerflow_state.target_delta <= 1
        assert 0 <= sample_deerflow_state.rebalance_threshold <= 1


# ============================================================================
# NODE TESTS
# ============================================================================

class TestOptionsAnalysisNode:
    """Test OptionsAnalysisNode functionality."""

    def test_options_analysis_returns_dict(self, sample_deerflow_state):
        """Test that options analysis node returns proper dict."""
        result = OptionsAnalysisNode.analyze(sample_deerflow_state.dict())
        
        assert isinstance(result, dict)
        assert "analyzed_options" in result
        assert "strategy_recommendations" in result

    def test_options_analysis_initializes(self):
        """Test that options analysis node can be instantiated."""
        node = OptionsAnalysisNode()
        assert node is not None


class TestStrategyBuilderNode:
    """Test StrategyBuilderNode functionality."""

    def test_strategy_builder_returns_dict(self, sample_deerflow_state):
        """Test that strategy builder node returns proper dict."""
        result = StrategyBuilderNode.build(sample_deerflow_state.dict())
        
        assert isinstance(result, dict)
        assert "constructed_strategies" in result
        assert "strategy_recommendations" in result

    def test_strategy_builder_initializes(self):
        """Test that strategy builder node can be instantiated."""
        node = StrategyBuilderNode()
        assert node is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
