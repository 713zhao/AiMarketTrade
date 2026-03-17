"""
Test suite for deerflow state schemas.
"""

import pytest
from datetime import datetime
from typing import List

from deerflow_openbb.state import (
    DeerflowState,
    TickerData,
    TechnicalAnalysis,
    FundamentalAnalysis,
    NewsAnalysis,
    GrowthAnalysis,
    RiskAnalysis,
    MacroAnalysis,
    ConsensusSignal,
    TradingDecision,
    AnalystType,
    SignalType,
    DataProvider,
)


class TestEnums:
    """Test enum definitions."""

    def test_analyst_type_values(self):
        """Test all analyst types are defined."""
        assert AnalystType.NEWS.value == "news"
        assert AnalystType.TECHNICAL.value == "technical"
        assert AnalystType.FUNDAMENTALS.value == "fundamentals"
        assert AnalystType.GROWTH.value == "growth"
        assert AnalystType.MACRO.value == "macro"
        assert AnalystType.RISK.value == "risk"
        assert AnalystType.PORTFOLIO.value == "portfolio"

    def test_signal_type_values(self):
        """Test all signal types are defined."""
        assert SignalType.BUY.value == "buy"
        assert SignalType.SELL.value == "sell"
        assert SignalType.HOLD.value == "hold"
        assert SignalType.STRONG_BUY.value == "strong_buy"
        assert SignalType.STRONG_SELL.value == "strong_sell"

    def test_data_provider_values(self):
        """Test data provider enum."""
        assert DataProvider.FMP.value == "fmp"
        assert DataProvider.POLYGON.value == "polygon"
        assert DataProvider.YAHOO.value == "yahoo"
        assert DataProvider.ALPHA_VANTAGE.value == "alpha_vantage"
        assert DataProvider.EODHD.value == "eodhd"


class TestTickerData:
    """Test TickerData model."""

    def test_create_minimal(self):
        """Create TickerData with minimal data."""
        ticker_data = TickerData(
            ticker="AAPL",
            provider=DataProvider.YAHOO
        )
        assert ticker_data.ticker == "AAPL"
        assert ticker_data.historical_data == {}
        assert ticker_data.data_quality_score == 1.0

    def test_has_sufficient_data_true(self):
        """Test when data is sufficient."""
        ticker_data = TickerData(
            ticker="AAPL",
            provider=DataProvider.YAHOO,
            historical_data={
                'close': [100.0] * 300,  # 300 data points
                'date': ['2024-01-01'] * 300
            }
        )
        assert ticker_data.has_sufficient_data(252) is True

    def test_has_sufficient_data_false(self):
        """Test when data is insufficient."""
        ticker_data = TickerData(
            ticker="AAPL",
            provider=DataProvider.YAHOO,
            historical_data={
                'close': [100.0] * 100,  # Only 100 points
            }
        )
        assert ticker_data.has_sufficient_data(252) is False

    def test_has_sufficient_data_empty(self):
        """Test when no data."""
        ticker_data = TickerData(ticker="AAPL", provider=DataProvider.YAHOO)
        assert ticker_data.has_sufficient_data() is False


class TestTechnicalAnalysis:
    """Test TechnicalAnalysis model."""

    def test_create_default(self):
        """Create with default values."""
        analysis = TechnicalAnalysis(ticker="AAPL")
        assert analysis.ticker == "AAPL"
        assert analysis.trend == "neutral"
        assert analysis.momentum == "neutral"
        assert analysis.confidence == 0.5
        assert analysis.analyst_type == AnalystType.TECHNICAL

    def test_custom_values(self):
        """Create with custom values."""
        analysis = TechnicalAnalysis(
            ticker="MSFT",
            trend="bullish",
            momentum="oversold",
            confidence=0.85,
            rsi_value=28.5,
            indicators={"SMA_20": [100.0, 101.0], "RSI_14": [28.5, 29.0]},
            signals=[{"type": "rsi_oversold", "signal": "buy", "strength": 0.7}],
        )
        assert analysis.trend == "bullish"
        assert analysis.momentum == "oversold"
        assert analysis.rsi_value == 28.5
        assert len(analysis.signals) == 1


class TestFundamentalAnalysis:
    """Test FundamentalAnalysis model."""

    def test_create(self):
        analysis = FundamentalAnalysis(
            ticker="GOOGL",
            pe_ratio=25.5,
            pb_ratio=4.2,
            roe=15.0,
            revenue_growth=12.5,
            valuation="fair",
            strengths=["Strong cash flow", "Market leader"],
            weaknesses=["High valuation"],
        )
        assert analysis.pe_ratio == 25.5
        assert analysis.roe == 15.0
        assert len(analysis.strengths) == 2
        assert analysis.valuation == "fair"


class TestNewsAnalysis:
    """Test NewsAnalysis model."""

    def test_create(self):
        analysis = NewsAnalysis(
            ticker="META",
            overall_sentiment=0.65,
            news_volume=25,
            recent_news_count=8,
            catalysts=[{"event": "product launch", "impact": "positive"}],
        )
        assert analysis.overall_sentiment == 0.65
        assert analysis.news_volume == 25
        assert len(analysis.catalysts) == 1


class TestStateSchemas:
    """Test all analysis state schemas."""

    def test_growth_analysis(self):
        growth = GrowthAnalysis(
            ticker="NVDA",
            revenue_growth_rate=35.5,
            growth_score=85.0,
        )
        assert growth.growth_score == 85.0

    def test_risk_analysis(self):
        risk = RiskAnalysis(
            ticker="AAPL",
            beta=1.2,
            volatility=0.28,
            risk_score=35.0,
            risk_level="low",
        )
        assert risk.beta == 1.2
        assert risk.risk_level == "low"

    def test_macro_analysis(self):
        macro = MacroAnalysis(
            ticker="JPM",
            sector="Financial Services",
            interest_rate_trend="rising",
            macro_score=60.0,
        )
        assert macro.sector == "Financial Services"

    def test_consensus_signal(self):
        consensus = ConsensusSignal(
            ticker="TSLA",
            overall_signal=SignalType.BUY,
            signal_strength=0.75,
        )
        assert consensus.overall_signal == SignalType.BUY

    def test_trading_decision(self):
        decision = TradingDecision(
            ticker="AMZN",
            action=SignalType.BUY,
            position_size=3.5,
            take_profit=180.0,
            rationale="Strong technical and fundamental signals",
        )
        assert decision.position_size == 3.5


class TestDeerflowState:
    """Test master state object."""

    def test_create_empty(self):
        """Create empty state."""
        state = DeerflowState()
        assert state.session_id == ""
        assert state.tickers == []
        assert len(state.ticker_data) == 0
        assert len(state.trading_decisions) == 0

    def test_create_with_tickers(self):
        """Create with tickers."""
        state = DeerflowState(
            tickers=["AAPL", "MSFT"],
            session_id="test_001"
        )
        assert len(state.tickers) == 2
        assert state.session_id == "test_001"

    def test_get_analyst_results(self):
        """Test getting results by ticker."""
        state = DeerflowState(tickers=["AAPL"])

        # Add some data
        tech = TechnicalAnalysis(ticker="AAPL", trend="bullish")
        state.technical_analyses["AAPL"] = tech

        results = state.get_analyst_results("AAPL")
        assert results["technical"] == tech
        assert results["fundamental"] is None

    def test_has_complete_analysis(self):
        """Test completeness check."""
        state = DeerflowState(tickers=["AAPL"])

        # Incomplete
        state.technical_analyses["AAPL"] = TechnicalAnalysis(ticker="AAPL")
        assert state.has_complete_analysis("AAPL") is False

        # Add fundamentals
        state.fundamental_analyses["AAPL"] = FundamentalAnalysis(ticker="AAPL")
        assert state.has_complete_analysis("AAPL") is False

        # Add news
        state.news_analyses["AAPL"] = NewsAnalysis(ticker="AAPL")
        assert state.has_complete_analysis("AAPL") is False

        # Add risk
        state.risk_analyses["AAPL"] = RiskAnalysis(ticker="AAPL")
        assert state.has_complete_analysis("AAPL") is True

    def test_add_error(self):
        """Test error logging."""
        state = DeerflowState()
        state.add_error("stock_data_node", "API timeout", "AAPL")

        assert "stock_data_node" in state.errors
        assert len(state.errors["stock_data_node"]) == 1
        assert state.errors["stock_data_node"][0]["ticker"] == "AAPL"

    def test_update_timestamp(self):
        """Test timestamp update."""
        state = DeerflowState()
        original = state.updated_at

        # Small delay
        import time
        time.sleep(0.01)

        state.update_timestamp()
        assert state.updated_at > original
