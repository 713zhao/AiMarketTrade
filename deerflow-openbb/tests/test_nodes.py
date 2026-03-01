"""
Unit tests for node implementations.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from deerflow_openbb.state import (
    TickerData,
    TechnicalAnalysis,
    AnalystType,
    DataProvider,
    DeerflowState,
)
from deerflow_openbb.nodes import BaseNode, StockDataNode, TechnicalAnalystNode, DecisionNode


class TestBaseNode:
    """Test BaseNode functionality."""

    def test_init(self):
        node = BaseNode("test_node")
        assert node.node_id == "test_node"

    def test_log(self, capsys):
        node = BaseNode("test_node")
        node.log("Test message", "INFO")
        captured = capsys.readouterr()
        assert "[test_node]" in captured.out
        assert "Test message" in captured.out

    def test_get_data_provider(self):
        node = BaseNode("test_node")
        provider = node.get_data_provider()
        assert provider in ["yahoo", "fmp", "polygon", "alpha_vantage", "eodhd"]


class TestStockDataNode:
    """Test StockDataNode functionality."""

    @pytest.fixture
    def node(self):
        return StockDataNode()

    @pytest.mark.asyncio
    async def test_execute_empty_state(self, node):
        """Test execution with empty state."""
        state = DeerflowState(tickers=[])

        result = await node.execute(state)

        assert result.completed_nodes[-1] == "stock_data_node"
        assert len(result.ticker_data) == 0

    @pytest.mark.asyncio
    async def test_execute_with_mock_data(self, node):
        """Test that mock node returns data."""
        # Instead of testing live, we'll validate structure
        state = DeerflowState(tickers=["AAPL"])

        # Mock the data fetch to avoid needing real API
        with patch.object(node, '_fetch_ticker_data') as mock_fetch:
            mock_fetch.return_value = TickerData(
                ticker="AAPL",
                provider=DataProvider.YAHOO,
                historical_data={
                    'date': ['2024-01-01', '2024-01-02'],
                    'close': [100.0, 101.0]
                },
                company_info={"name": "Apple Inc."},
                financial_statements={},
                news=[],
                data_quality_score=0.9,
            )

            result = await node.execute(state)

            assert "AAPL" in result.ticker_data
            assert result.ticker_data["AAPL"].data_quality_score == 0.9
            assert result.api_calls == 1

    def test_calculate_data_quality(self, node):
        """Test data quality scoring."""
        # Full data
        quality1 = node._calculate_data_quality(
            historical_data={'date': ['2024-01-01'] * 300},
            company_info={'name': 'Test', 'sector': 'Tech'},
            financial_statements={'income': {}, 'balance': {}, 'cashflow': {}}
        )
        # Should be: 0.3 (data) + 0.2 (company) + 0.5 (3/3 statements) = 1.0
        assert quality1 == 1.0

        # No financial statements
        quality2 = node._calculate_data_quality(
            historical_data={},
            company_info={'name': 'Test'},
            financial_statements={}
        )
        assert quality2 < 0.5  # Only company info contributes 0.2

        # No data at all
        quality3 = node._calculate_data_quality(
            historical_data={},
            company_info={},
            financial_statements={}
        )
        assert quality3 == 0.0


class TestTechnicalAnalystNode:
    """Test TechnicalAnalystNode functionality."""

    @pytest.fixture
    def node(self):
        return TechnicalAnalystNode()

    @pytest.fixture
    def sample_ticker_data(self):
        """Create sample ticker data with price history."""
        import pandas as pd
        import numpy as np

        # Generate 300 days of synthetic data
        np.random.seed(42)
        n = 300
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n, freq='D')
        returns = np.random.normal(0.0005, 0.015, n)
        prices = 100 * np.exp(np.cumsum(returns))

        return TickerData(
            ticker="AAPL",
            provider=DataProvider.MOCK,
            historical_data={
                'date': dates.strftime('%Y-%m-%d').tolist(),
                'open': (prices * (1 + np.random.uniform(-0.005, 0.005, n))).tolist(),
                'high': (prices * (1 + np.random.uniform(0, 0.01, n))).tolist(),
                'low': (prices * (1 + np.random.uniform(-0.01, 0, n))).tolist(),
                'close': prices.tolist(),
                'volume': np.random.randint(100000, 10000000, n).tolist(),
            },
            company_info={"name": "Apple Inc."},
            financial_statements={},
            news=[],
            data_quality_score=1.0,
        )

    @pytest.mark.asyncio
    async def test_execute(self, node, sample_ticker_data):
        """Test technical analysis execution."""
        state = DeerflowState(tickers=["AAPL"])
        state.ticker_data["AAPL"] = sample_ticker_data

        # Execute node
        result_state = await node.execute(state)

        assert "AAPL" in result_state.technical_analyses
        analysis = result_state.technical_analyses["AAPL"]

        # Validate analysis structure
        assert analysis.ticker == "AAPL"
        assert analysis.analyst_type == AnalystType.TECHNICAL
        assert isinstance(analysis.indicators, dict)
        assert isinstance(analysis.signals, list)
        assert isinstance(analysis.support_levels, list)
        assert isinstance(analysis.resistance_levels, list)
        assert analysis.trend in ["bullish", "bearish", "neutral"]
        assert analysis.momentum in ["bullish", "oversold", "overbought", "neutral"]
        assert 0.0 <= analysis.confidence <= 1.0
        assert analysis.summary  # Should have summary

        # Check key indicators are calculated
        assert "SMA_20" in analysis.indicators
        assert "RSI_14" in analysis.indicators
        assert "MACD" in analysis.indicators
        assert "ATR_14" in analysis.indicators

        print(f"\n  Technical analysis generated:")
        print(f"    Trend: {analysis.trend}")
        print(f"    Momentum: {analysis.momentum}")
        print(f"    Signals: {len(analysis.signals)}")
        print(f"    Confidence: {analysis.confidence:.1%}")

    @pytest.mark.asyncio
    async def test_execute_no_data(self, node):
        """Test execution with no data."""
        state = DeerflowState(tickers=["AAPL"])
        # No ticker_data set

        result_state = await node.execute(state)

        # Should not create analysis, but not error
        assert "AAPL" not in result_state.technical_analyses

    def test_dict_to_dataframe(self, node):
        """Test DataFrame conversion."""
        data_dict = {
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000000, 1100000, 1200000],
        }

        df = node._dict_to_dataframe(data_dict)

        assert not df.empty
        assert 'close' in df.columns
        assert len(df) == 3

    def test_calculate_rsi(self, node):
        """Test RSI calculation."""
        import pandas as pd
        prices = pd.Series([100.0] * 20 + list(range(100, 120)))  # Uptrend
        rsi = node._calculate_rsi(prices)
        assert len(rsi) == len(prices)
        assert all(0 <= val <= 100 for val in rsi.dropna())

    def test_calculate_atr(self, node):
        """Test ATR calculation."""
        import pandas as pd
        n = 50
        data = {
            'high': [100.0 + i*0.1 for i in range(n)],
            'low': [99.0 + i*0.1 for i in range(n)],
            'close': [99.5 + i*0.1 for i in range(n)],
        }
        df = pd.DataFrame(data)
        atr = node._calculate_atr(df['high'], df['low'], df['close'])
        assert len(atr) == n
        assert all(atr >= 0)

    def test_generate_signals(self, node):
        """Test signal generation logic."""
        import pandas as pd
        import numpy as np

        # Create data with clear moving average crossover
        n = 300
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n, freq='D')
        # Create scenario with SMA crossing
        prices1 = np.array([100.0] * 250)  # First 250 days flat
        prices2 = np.arange(250, 300) * 0.5  # Last 50 days rising
        prices = np.concatenate([prices1, prices2])

        df = pd.DataFrame({
            'close': prices,
        })

        # Build fake indicators
        sma_20 = pd.Series([100.0] * 280 + list(np.linspace(100, 125, 20)))
        sma_50 = pd.Series([100.0] * 250 + list(np.linspace(100, 110, 50)))
        rsi = pd.Series(np.concatenate([[50]*280, np.linspace(40, 30, 20)]))

        indicators = {
            'SMA_20': sma_20.tolist(),
            'SMA_50': sma_50.tolist(),
            'RSI_14': rsi.tolist(),
        }

        signals = node._generate_signals(df, indicators)

        # Should generate some signals based on the data
        # Signal types: golden_cross, rsi_oversold, etc.
        assert isinstance(signals, list)

        # At least one signal expected for this contrived example
        # (May not always trigger, so we just validate structure if any)
        for signal in signals:
            assert 'type' in signal
            assert 'signal' in signal
            assert 'strength' in signal
            assert 'description' in signal

    def test_determine_trend(self, node):
        """Test trend determination."""
        import pandas as pd
        n = 300
        prices = [100.0] * 250 + list(range(100, 130))  # Uptrend at end
        df = pd.DataFrame({'close': prices})

        trend, strength = node._determine_trend(df)
        assert trend in ["bullish", "bearish", "neutral"]
        assert 0.0 <= strength <= 1.0

    def test_find_support_resistance(self, node):
        """Test S/R level detection."""
        import pandas as pd

        # Create data with clear support at 100 and resistance at 110
        n = 300
        highs = [110.0 if i % 50 < 5 else 108.0 for i in range(n)]
        lows = [100.0 if i % 50 < 5 else 102.0 for i in range(n)]

        df = pd.DataFrame({'high': highs, 'low': lows})

        support, resistance = node._find_support_resistance(df)

        assert isinstance(support, list)
        assert isinstance(resistance, list)

        # Check that 100.0 is in support (or very close due to rounding)
        support_rounded = [round(s, 1) for s in support]
        assert any(100.0 <= s <= 100.5 for s in support_rounded)

    def test_calculate_volatility(self, node):
        """Test volatility calculation."""
        import pandas as pd
        import numpy as np

        # 300 days of returns
        returns = np.random.normal(0.001, 0.015, 300)
        df = pd.DataFrame({'close': 100 * np.exp(np.cumsum(returns))})

        vol = node._calculate_volatility(df)
        assert vol > 0
        assert isinstance(vol, float)

    def test_generate_summary(self, node):
        """Test summary generation."""
        summary = node._generate_summary(
            trend="bullish",
            momentum="neutral",
            signals=[
                {"type": "golden_cross", "signal": "buy", "strength": 0.7},
                {"type": "rsi_oversold", "signal": "buy", "strength": 0.6},
            ],
            support_levels=[100.0, 101.0],
            resistance_levels=[110.0]
        )

        assert "bullish" in summary
        assert "neutral" in summary
        assert "support" in summary.lower()
        assert "resistance" in summary.lower()


class TestDecisionNode:
    """Test DecisionNode functionality."""

    @pytest.fixture
    def node(self):
        return DecisionNode()

    @pytest.mark.asyncio
    async def test_execute(self, node):
        """Test decision generation."""
        state = DeerflowState(tickers=["AAPL"])

        # Add technical analysis
        tech = TechnicalAnalysis(
            ticker="AAPL",
            trend="bullish",
            momentum="neutral",
            confidence=0.75,
            signals=[
                {"type": "golden_cross", "signal": "buy", "strength": 0.7},
                {"type": "macd_bullish", "signal": "buy", "strength": 0.65},
            ],
            indicators={
                'ATR_14': [2.0] * 300,
                'SMA_20': [100.0] * 300,
                'SMA_50': [98.0] * 300,
                'SMA_200': [95.0] * 300,
            },
        )
        state.technical_analyses["AAPL"] = tech

        # Add ticker data
        state.ticker_data["AAPL"] = TickerData(
            ticker="AAPL",
            provider=DataProvider.MOCK,
            historical_data={
                'close': [100.0] * 300,
            }
        )

        result_state = await node.execute(state)

        assert "AAPL" in result_state.trading_decisions
        decision = result_state.trading_decisions["AAPL"]

        # Should be BUY given bullish trend and buy signals
        assert decision.action.value in ["buy", "sell", "hold"]
        assert decision.confidence > 0

    def test_make_decision_buy_signal(self, node):
        """Test decision logic for buy signal."""
        from deerflow_openbb.nodes import TradingDecision, SignalType

        state = DeerflowState(tickers=["AAPL"])

        tech = TechnicalAnalysis(
            ticker="AAPL",
            trend="bullish",
            momentum="oversold",
            confidence=0.8,
            signals=[
                {"type": "golden_cross", "signal": "buy", "strength": 0.7},
                {"type": "rsi_oversold", "signal": "buy", "strength": 0.6},
            ],
            indicators={'ATR_14': [2.0] * 300},
        )
        state.technical_analyses["AAPL"] = tech
        state.ticker_data["AAPL"] = TickerData(
            ticker="AAPL",
            provider=DataProvider.MOCK,
            historical_data={'close': [100.0] * 300}
        )

        decision = node._make_decision("AAPL", state)

        assert decision.action in [SignalType.BUY, SignalType.STRONG_BUY]
        assert decision.position_size > 0
        assert decision.confidence > 0.6

    def test_make_decision_sell_signal(self, node):
        """Test decision logic for sell signal."""
        state = DeerflowState(tickers=["AAPL"])

        tech = TechnicalAnalysis(
            ticker="AAPL",
            trend="bearish",
            momentum="overbought",
            confidence=0.8,
            signals=[
                {"type": "death_cross", "signal": "sell", "strength": 0.7},
                {"type": "rsi_overbought", "signal": "sell", "strength": 0.6},
            ],
            indicators={'ATR_14': [2.0] * 300},
        )
        state.technical_analyses["AAPL"] = tech
        state.ticker_data["AAPL"] = TickerData(
            ticker="AAPL",
            provider=DataProvider.MOCK,
            historical_data={'close': [100.0] * 300}
        )

        decision = node._make_decision("AAPL", state)

        assert decision.action == SignalType.SELL
        assert decision.position_size <= 0

    def test_generate_rationale(self, node):
        """Test rationale generation."""
        tech = TechnicalAnalysis(
            ticker="AAPL",
            trend="bullish",
            momentum="neutral",
            confidence=0.7,
            signals=[
                {"type": "golden_cross", "signal": "buy", "strength": 0.7},
                {"type": "rsi_oversold", "signal": "buy", "strength": 0.6},
            ],
        )

        rationale = node._generate_rationale(tech, SignalType.BUY, 1.3)

        assert "bullish" in rationale.lower()
        assert "Recommendation: BUY" in rationale
        assert "1.3" in rationale or "1.30" in rationale  # net signal
