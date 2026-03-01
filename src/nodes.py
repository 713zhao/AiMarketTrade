"""
Node implementations for deerflow graph.

This module contains the core nodes that perform specific tasks:
- StockDataNode: Fetches market data via OpenBB
- TechnicalAnalystNode: Performs technical analysis
- DecisionNode: Synthesizes results into trading decisions
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from openbb import obb
import pandas as pd
import numpy as np

from .state import (
    DeerflowState,
    TickerData,
    TechnicalAnalysis,
    AnalystType,
    DataProvider,
    SignalType,
    get_settings,
)


class BaseNode:
    """
    Base class for all graph nodes.

    Provides common functionality like logging, error handling,
    and state management.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.settings = get_settings()

    async def execute(self, state: DeerflowState) -> DeerflowState:
        """
        Execute the node's main logic.

        Should be implemented by subclasses. This base method handles
        common error handling and state updates.
        """
        try:
            state = await self._execute(state)
            state.completed_nodes.append(self.node_id)
        except Exception as e:
            state.add_error(self.node_id, str(e))
            raise
        finally:
            state.update_timestamp()
        return state

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Subclass implementation of node logic."""
        raise NotImplementedError("Subclasses must implement _execute method")

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message with node identifier."""
        print(f"[{self.node_id}] {level}: {message}")

    def get_data_provider(self) -> str:
        """Get the primary data provider to use."""
        return self.settings.get_primary_data_provider()


class StockDataNode(BaseNode):
    """
    Node responsible for fetching market data using OpenBB.

    Handles multiple data providers with fallback logic, data
    normalization, and quality scoring.
    """

    def __init__(self):
        super().__init__("stock_data_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Fetch data for all tickers in the state."""
        self.log(f"Fetching data for {len(state.tickers)} tickers")

        provider = self.get_data_provider()
        self.log(f"Using data provider: {provider}")

        for ticker in state.tickers:
            try:
                self.log(f"Fetching data for {ticker}")
                ticker_data = await self._fetch_ticker_data(ticker, provider)
                state.ticker_data[ticker] = ticker_data
                state.api_calls += 1
                self.log(f"Successfully fetched {len(ticker_data.historical_data)} records for {ticker}")
            except Exception as e:
                self.log(f"Error fetching data for {ticker}: {e}", "ERROR")
                state.add_error(self.node_id, str(e), ticker)
                continue

        self.log(f"Completed data fetch: {len(state.ticker_data)}/{len(state.tickers)} tickers")
        return state

    async def _fetch_ticker_data(self, ticker: str, provider: str) -> TickerData:
        """
        Fetch comprehensive data for a single ticker.

        Uses asyncio.gather to fetch different data types concurrently.
        """
        # Fetch historical price data
        historical_data = await self._fetch_historical_data(ticker, provider)

        # Fetch company info
        company_info = await self._fetch_company_info(ticker, provider)

        # Fetch financial statements (if available)
        financial_statements = await self._fetch_financial_statements(ticker, provider)

        # Fetch news (if available and configured)
        news = await self._fetch_news(ticker, provider)

        # Calculate data quality score
        data_quality_score = self._calculate_data_quality(
            historical_data, company_info, financial_statements
        )

        return TickerData(
            ticker=ticker,
            provider=DataProvider(provider),
            historical_data=historical_data,
            company_info=company_info,
            financial_statements=financial_statements,
            news=news,
            data_quality_score=data_quality_score,
        )

    async def _fetch_historical_data(
        self,
        ticker: str,
        provider: str,
        period: str = "2y",
        interval: str = "1d"
    ) -> Dict[str, List[Any]]:
        """Fetch historical OHLCV data."""
        loop = asyncio.get_event_loop()

        def fetch():
            try:
                # Use OpenBB's unified API
                result = obb.equity.price.historical(
                    symbol=ticker,
                    provider=provider if provider != "yahoo" else "yfinance",
                    period=period,
                    interval=interval,
                )

                if result.empty:
                    return {}

                # Convert to dict with lists (easier to serialize)
                df = result.reset_index()
                data_dict = {}

                for col in df.columns:
                    col_lower = col.lower()
                    if 'date' in col_lower or 'time' in col_lower:
                        data_dict['date'] = df[col].dt.strftime('%Y-%m-%d').tolist()
                    else:
                        data_dict[col] = df[col].tolist()

                return data_dict

            except Exception as e:
                self.log(f"Error fetching historical data for {ticker}: {e}", "ERROR")
                return {}

        return await loop.run_in_executor(None, fetch)

    async def _fetch_company_info(self, ticker: str, provider: str) -> Dict[str, Any]:
        """Fetch company information."""
        loop = asyncio.get_event_loop()

        def fetch():
            try:
                result = obb.equity.overview(symbol=ticker, provider=provider if provider != "yahoo" else "yfinance")
                if result.empty:
                    return {}
                # Convert Series to dict, handling nested structures
                return result.to_dict()
            except Exception as e:
                self.log(f"Error fetching company info for {ticker}: {e}", "WARNING")
                return {}

        return await loop.run_in_executor(None, fetch)

    async def _fetch_financial_statements(
        self,
        ticker: str,
        provider: str
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch financial statements (income, balance, cash flow)."""
        loop = asyncio.get_event_loop()

        def fetch():
            statements = {}
            try:
                # Income statement
                income = obb.equity.financials.income(symbol=ticker, provider=provider if provider != "yahoo" else "yfinance")
                if not income.empty:
                    statements["income"] = income.to_dict()

                # Balance sheet
                balance = obb.equity.financials.balance(symbol=ticker, provider=provider if provider != "yahoo" else "yfinance")
                if not balance.empty:
                    statements["balance"] = balance.to_dict()

                # Cash flow
                cashflow = obb.equity.financials.cash(symbol=ticker, provider=provider if provider != "yahoo" else "yfinance")
                if not cashflow.empty:
                    statements["cashflow"] = cashflow.to_dict()

            except Exception as e:
                self.log(f"Error fetching financial statements for {ticker}: {e}", "WARNING")
                return {}

            return statements

        return await loop.run_in_executor(None, fetch)

    async def _fetch_news(self, ticker: str, provider: str) -> List[Dict[str, Any]]:
        """Fetch recent news for the ticker."""
        loop = asyncio.get_event_loop()

        def fetch():
            try:
                if provider in ["fmp", "benzinga", "polygon"]:
                    result = obb.news.company(
                        symbol=ticker,
                        provider=provider,
                        limit=20
                    )
                else:
                    # Yahoo news might be limited
                    result = obb.news.company(symbol=ticker, provider="yfinance", limit=10)

                if result.empty:
                    return []

                news_list = []
                for _, row in result.iterrows():
                    news_list.append({
                        "title": row.get("title", ""),
                        "description": row.get("description", ""),
                        "source": row.get("source", ""),
                        "published_at": str(row.get("published", "")),
                        "url": row.get("url", ""),
                    })

                return news_list

            except Exception as e:
                self.log(f"Error fetching news for {ticker}: {e}", "WARNING")
                return []

        return await loop.run_in_executor(None, fetch)

    def _calculate_data_quality(
        self,
        historical_data: Dict[str, List[Any]],
        company_info: Dict[str, Any],
        financial_statements: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Calculate a data quality score (0-1) based on completeness.

        Factors:
        - Historical data completeness (price: 30%)
        - Company info presence (20%)
        - Financial statements presence (50%)
        """
        score = 0.0

        # Historical data (30%)
        if historical_data and len(historical_data.get('date', [])) >= 252:
            score += 0.3
        elif historical_data:
            score += 0.2

        # Company info (20%)
        if company_info and len(company_info) > 5:
            score += 0.2

        # Financial statements (50%)
        if financial_statements:
            stmt_count = len(financial_statements)
            score += 0.5 * (stmt_count / 3)  # 3 is max (income, balance, cashflow)

        return min(1.0, score)


class TechnicalAnalystNode(BaseNode):
    """
    Technical analysis agent that analyzes price patterns and indicators.

    Calculates technical indicators, identifies support/resistance,
    and generates trading signals based on price action.
    """

    def __init__(self):
        super().__init__("technical_analyst_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Perform technical analysis on all tickers with data."""
        self.log(f"Performing technical analysis")

        for ticker, ticker_data in state.ticker_data.items():
            if not ticker_data.historical_data:
                self.log(f"Skipping {ticker}: no historical data", "WARNING")
                continue

            try:
                self.log(f"Analyzing {ticker}")
                analysis = await self._analyze_ticker(ticker, ticker_data)
                state.technical_analyses[ticker] = analysis
                self.log(f"Completed technical analysis for {ticker}")
            except Exception as e:
                self.log(f"Error in technical analysis for {ticker}: {e}", "ERROR")
                state.add_error(self.node_id, str(e), ticker)

        self.log(f"Completed technical analysis: {len(state.technical_analyses)} tickers")
        return state

    async def _analyze_ticker(self, ticker: str, ticker_data: TickerData) -> TechnicalAnalysis:
        """Perform comprehensive technical analysis for a single ticker."""
        # Convert historical data to DataFrame
        df = self._dict_to_dataframe(ticker_data.historical_data)

        if df.empty:
            raise ValueError(f"No price data available for {ticker}")

        # Calculate all indicators
        indicators = self._calculate_indicators(df)

        # Generate signals
        signals = self._generate_signals(df, indicators)

        # Identify support/resistance
        support_levels, resistance_levels = self._find_support_resistance(df)

        # Determine trend
        trend, trend_strength = self._determine_trend(df)

        # Calculate momentum
        momentum, rsi = self._calculate_momentum(df)

        # Calculate volatility
        volatility = self._calculate_volatility(df)

        # Generate summary
        summary = self._generate_summary(
            trend=trend,
            momentum=momentum,
            signals=signals,
            support_levels=support_levels,
            resistance_levels=resistance_levels
        )

        # Calculate confidence
        confidence = self._calculate_confidence(df, signals, trend_strength)

        return TechnicalAnalysis(
            ticker=ticker,
            indicators=indicators,
            signals=signals,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            trend=trend,
            trend_strength=trend_strength,
            momentum=momentum,
            rsi_value=rsi,
            volatility=volatility,
            summary=summary,
            confidence=confidence,
        )

    def _dict_to_dataframe(self, data_dict: Dict[str, List[Any]]) -> pd.DataFrame:
        """Convert dictionary data back to pandas DataFrame."""
        if 'date' not in data_dict:
            return pd.DataFrame()

        df = pd.DataFrame(data_dict)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        # Ensure we have OHLCV columns (various possible names)
        column_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'open' in col_lower:
                column_map[col] = 'open'
            elif 'high' in col_lower:
                column_map[col] = 'high'
            elif 'low' in col_lower:
                column_map[col] = 'low'
            elif 'close' in col_lower:
                column_map[col] = 'close'
            elif 'volume' in col_lower:
                column_map[col] = 'volume'

        df.rename(columns=column_map, inplace=True)

        # Keep only mapped columns
        keep_cols = ['open', 'high', 'low', 'close', 'volume']
        df = df[[c for c in keep_cols if c in df.columns]]

        return df.dropna()

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        """Calculate technical indicators."""
        indicators = {}

        if 'close' not in df.columns:
            return indicators

        close = df['close']
        high = df.get('high', close)
        low = df.get('low', close)
        volume = df.get('volume', pd.Series([0] * len(df)))

        # Moving averages
        indicators['SMA_20'] = close.rolling(20).mean().tolist()
        indicators['SMA_50'] = close.rolling(50).mean().tolist()
        indicators['SMA_200'] = close.rolling(200).mean().tolist()
        indicators['EMA_12'] = close.ewm(span=12, adjust=False).mean().tolist()
        indicators['EMA_26'] = close.ewm(span=26, adjust=False).mean().tolist()

        # RSI
        indicators['RSI_14'] = self._calculate_rsi(close).tolist()

        # MACD
        macd_line = indicators['EMA_12'] - indicators['EMA_26']
        signal_line = pd.Series(macd_line).ewm(span=9, adjust=False).mean().tolist()
        indicators['MACD'] = macd_line.tolist()
        indicators['MACD_SIGNAL'] = signal_line
        indicators['MACD_HIST'] = (pd.Series(macd_line) - pd.Series(signal_line)).tolist()

        # Bollinger Bands
        sma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        indicators['BB_UPPER'] = (sma_20 + 2 * std_20).tolist()
        indicators['BB_MIDDLE'] = sma_20.tolist()
        indicators['BB_LOWER'] = (sma_20 - 2 * std_20).tolist()

        # ATR (Average True Range)
        indicators['ATR_14'] = self._calculate_atr(high, low, close).tolist()

        # Volume-based indicators
        indicators['VOLUME_SMA'] = volume.rolling(20).mean().tolist()

        return indicators

    def _calculate_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr.fillna(0)

    def _generate_signals(self, df: pd.DataFrame, indicators: Dict[str, List[float]]) -> List[Dict[str, Any]]:
        """Generate buy/sell signals based on indicator combinations."""
        signals = []
        close = df['close']

        # Convert indicators to Series for easier access
        sma_20 = pd.Series(indicators.get('SMA_20', []))
        sma_50 = pd.Series(indicators.get('SMA_50', []))
        sma_200 = pd.Series(indicators.get('SMA_200', []))
        rsi = pd.Series(indicators.get('RSI_14', []))
        macd_line = pd.Series(indicators.get('MACD', []))
        macd_signal = pd.Series(indicators.get('MACD_SIGNAL', []))
        bb_upper = pd.Series(indicators.get('BB_UPPER', []))
        bb_lower = pd.Series(indicators.get('BB_LOWER', []))

        # Current values (most recent)
        current_close = close.iloc[-1] if len(close) > 0 else None
        current_sma20 = sma_20.iloc[-1] if len(sma_20) > 0 else None
        current_sma50 = sma_50.iloc[-1] if len(sma_50) > 0 else None
        current_sma200 = sma_200.iloc[-1] if len(sma_200) > 0 else None
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else None
        current_macd = macd_line.iloc[-1] if len(macd_line) > 0 else None
        current_macd_signal = macd_signal.iloc[-1] if len(macd_signal) > 0 else None
        current_bb_upper = bb_upper.iloc[-1] if len(bb_upper) > 0 else None
        current_bb_lower = bb_lower.iloc[-1] if len(bb_lower) > 0 else None

        if None in [current_close, current_sma20, current_sma50]:
            return signals

        # Signal 1: Golden Cross / Death Cross (SMA 50 vs 200)
        if len(sma_50) > 1 and len(sma_200) > 1:
            sma50_prev = sma_50.iloc[-2]
            sma200_prev = sma_200.iloc[-2]

            if sma50_prev <= sma200_prev and sma50 > sma200:
                signals.append({
                    "type": "golden_cross",
                    "signal": "buy",
                    "strength": 0.7,
                    "description": "SMA 50 crossed above SMA 200 (bullish)"
                })
            elif sma50_prev >= sma200_prev and sma50 < sma200:
                signals.append({
                    "type": "death_cross",
                    "signal": "sell",
                    "strength": 0.7,
                    "description": "SMA 50 crossed below SMA 200 (bearish)"
                })

        # Signal 2: RSI oversold/overbought
        if current_rsi is not None:
            if current_rsi < 30:
                signals.append({
                    "type": "rsi_oversold",
                    "signal": "buy",
                    "strength": 0.6,
                    "description": f"RSI at {current_rsi:.1f} indicates oversold conditions"
                })
            elif current_rsi > 70:
                signals.append({
                    "type": "rsi_overbought",
                    "signal": "sell",
                    "strength": 0.6,
                    "description": f"RSI at {current_rsi:.1f} indicates overbought conditions"
                })

        # Signal 3: MACD crossover
        if len(macd_line) > 1 and len(macd_signal) > 1:
            macd_prev = macd_line.iloc[-2]
            macd_signal_prev = macd_signal.iloc[-2]

            if macd_prev <= macd_signal_prev and macd > macd_signal:
                signals.append({
                    "type": "macd_bullish",
                    "signal": "buy",
                    "strength": 0.65,
                    "description": "MACD crossed above signal line (bullish)"
                })
            elif macd_prev >= macd_signal_prev and macd < macd_signal:
                signals.append({
                    "type": "macd_bearish",
                    "signal": "sell",
                    "strength": 0.65,
                    "description": "MACD crossed below signal line (bearish)"
                })

        # Signal 4: Price near Bollinger Bands
        if current_bb_upper and current_bb_lower and current_close:
            bb_position = (current_close - current_bb_lower) / (current_bb_upper - current_bb_lower)
            if bb_position > 0.95:
                signals.append({
                    "type": "bb_overextended",
                    "signal": "sell",
                    "strength": 0.5,
                    "description": f"Price near upper Bollinger Band ({bb_position:.2f})"
                })
            elif bb_position < 0.05:
                signals.append({
                    "type": "bb_oversold",
                    "signal": "buy",
                    "strength": 0.5,
                    "description": f"Price near lower Bollinger Band ({bb_position:.2f})"
                })

        # Signal 5: Moving average slope
        if len(sma_20) > 20:
            sma20_slope = (sma_20.iloc[-1] - sma_20.iloc[-20]) / sma_20.iloc[-20]
            if sma20_slope > 0.02:
                signals.append({
                    "type": "sma20_rising",
                    "signal": "buy",
                    "strength": 0.55,
                    "description": f"SMA 20 rising {sma20_slope:.1%} over 20 periods"
                })
            elif sma20_slope < -0.02:
                signals.append({
                    "type": "sma20_falling",
                    "signal": "sell",
                    "strength": 0.55,
                    "description": f"SMA 20 falling {sma20_slope:.1%} over 20 periods"
                })

        return signals

    def _find_support_resistance(
        self,
        df: pd.DataFrame,
        window: int = 20
    ) -> tuple[List[float], List[float]]:
        """
        Find support and resistance levels using local minima/maxima.

        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        if 'high' not in df.columns or 'low' not in df.columns:
            return [], []

        highs = df['high'].values
        lows = df['low'].values

        support_levels = []
        resistance_levels = []

        # Find local minima for support
        for i in range(window, len(lows) - window):
            if all(lows[i] <= lows[i - j] for j in range(1, window + 1)) and \
               all(lows[i] <= lows[i + j] for j in range(1, window + 1)):
                support_levels.append(round(float(lows[i]), 2))

        # Find local maxima for resistance
        for i in range(window, len(highs) - window):
            if all(highs[i] >= highs[i - j] for j in range(1, window + 1)) and \
               all(highs[i] >= highs[i + j] for j in range(1, window + 1)):
                resistance_levels.append(round(float(highs[i]), 2))

        # Remove close duplicates and sort
        support_levels = sorted(set([round(s, 2) for s in support_levels]))
        resistance_levels = sorted(set([round(r, 2) for r in resistance_levels]))

        # Keep only the most recent levels (max 5 each)
        return support_levels[-5:], resistance_levels[-5:]

    def _determine_trend(self, df: pd.DataFrame) -> tuple[str, float]:
        """Determine the current trend and its strength."""
        close = df['close']

        if len(close) < 200:
            return "neutral", 0.5

        # Moving average trend
        sma_20 = close.rolling(20).mean().iloc[-1]
        sma_50 = close.rolling(50).mean().iloc[-1]
        sma_200 = close.rolling(200).mean().iloc[-1]
        current_price = close.iloc[-1]

        # Calculate slopes
        sma20_slope = (close.rolling(20).mean().iloc[-1] - close.rolling(20).mean().iloc[-5]) / close.rolling(20).mean().iloc[-5]
        sma50_slope = (close.rolling(50).mean().iloc[-1] - close.rolling(50).mean().iloc[-10]) / close.rolling(50).mean().iloc[-10]

        # Trend determination
        if current_price > sma_20 > sma_50 > sma_200 and sma20_slope > 0.01 and sma50_slope > 0.005:
            return "bullish", 0.9
        elif current_price < sma_20 < sma_50 < sma_200 and sma20_slope < -0.01 and sma50_slope < -0.005:
            return "bearish", 0.9
        elif current_price > sma_200 and sma20_slope > 0:
            return "bullish", 0.6
        elif current_price < sma_200 and sma20_slope < 0:
            return "bearish", 0.6
        else:
            return "neutral", 0.5

    def _calculate_momentum(self, df: pd.DataFrame) -> tuple[str, Optional[float]]:
        """Calculate momentum state using RSI."""
        close = df['close']
        rsi = self._calculate_rsi(close).iloc[-1] if len(close) >= 14 else 50

        if rsi < 30:
            return "oversold", float(rsi)
        elif rsi > 70:
            return "overbought", float(rsi)
        else:
            return "neutral", float(rsi)

    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate annualized volatility."""
        if 'close' not in df.columns or len(df) < 20:
            return 0.0

        returns = df['close'].pct_change().dropna()
        if len(returns) < 20:
            return 0.0

        daily_vol = returns.rolling(20).std().iloc[-1]
        annualized_vol = daily_vol * np.sqrt(252)
        return float(annualized_vol)

    def _generate_summary(
        self,
        trend: str,
        momentum: str,
        signals: List[Dict[str, Any]],
        support_levels: List[float],
        resistance_levels: List[float]
    ) -> str:
        """Generate a narrative summary of the technical analysis."""
        parts = []

        parts.append(f"The stock is in a {trend} trend with {momentum} momentum.")

        if signals:
            buy_signals = [s for s in signals if s['signal'] == 'buy']
            sell_signals = [s for s in signals if s['signal'] == 'sell']

            if buy_signals:
                parts.append(f"Identified {len(buy_signals)} bullish signals including {', '.join(s['type'] for s in buy_signals[:2])}.")
            if sell_signals:
                parts.append(f"Identified {len(sell_signals)} bearish signals including {', '.join(s['type'] for s in sell_signals[:2])}.")

        if support_levels:
            parts.append(f"Key support levels: ${', $'.join(str(s) for s in support_levels[:3])}.")
        if resistance_levels:
            parts.append(f"Key resistance levels: ${', $'.join(str(r) for r in resistance_levels[:3])}.")

        return " ".join(parts)

    def _calculate_confidence(
        self,
        df: pd.DataFrame,
        signals: List[Dict[str, Any]],
        trend_strength: float
    ) -> float:
        """
        Calculate confidence in the technical analysis.

        Factors:
        - Trend strength (40%)
        - Signal consistency (30%)
        - Data quality (30%)
        """
        base_confidence = trend_strength * 0.4

        # Check signal consistency (more aligned signals = higher confidence)
        if signals:
            buy_strength = sum(s['strength'] for s in signals if s['signal'] == 'buy')
            sell_strength = sum(s['strength'] for s in signals if s['signal'] == 'sell')

            # If signals are aligned (mostly buys or mostly sells), boost confidence
            max_strength = max(buy_strength, sell_strength)
            total_strength = buy_strength + sell_strength

            if total_strength > 0:
                alignment = max_strength / total_strength
                base_confidence += alignment * 0.3

        # Data quality (enough data points)
        data_quality = min(1.0, len(df) / 252) * 0.3
        base_confidence += data_quality

        return min(1.0, base_confidence)


class NewsAnalystNode(BaseNode):
    """
    News analysis agent that processes news articles for sentiment and catalysts.

    Analyzes recent news, press releases, and social media mentions
    to identify market-moving events and sentiment trends.
    """

    def __init__(self):
        super().__init__("news_analyst_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Perform news sentiment analysis on all tickers with news data."""
        self.log(f"Performing news analysis")

        for ticker, ticker_data in state.ticker_data.items():
            if not ticker_data.news:
                self.log(f"Skipping {ticker}: no news data", "WARNING")
                continue

            try:
                self.log(f"Analyzing news for {ticker} ({len(ticker_data.news)} articles)")
                analysis = await self._analyze_news(ticker, ticker_data.news)
                state.news_analyses[ticker] = analysis
                self.log(f"News sentiment for {ticker}: {analysis.overall_sentiment:.2f}")
            except Exception as e:
                self.log(f"Error in news analysis for {ticker}: {e}", "ERROR")
                state.add_error(self.node_id, str(e), ticker)

        self.log(f"Completed news analysis: {len(state.news_analyses)} tickers")
        return state

    async def _analyze_news(self, ticker: str, news_articles: List[Dict[str, Any]]) -> NewsAnalysis:
        """Analyze news articles for sentiment, catalysts, and key events."""
        import re
        from datetime import datetime, timedelta

        if not news_articles:
            return NewsAnalysis(ticker=ticker)

        sentiments = []
        catalysts = []
        key_events = []
        risk_events = []
        key_entities = set()

        # Recent cutoff (7 days ago)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)

        recent_count = 0

        for article in news_articles:
            # Extract text
            title = article.get("title", "")
            description = article.get("description", "")
            text = f"{title} {description}".lower()

            # Skip if no meaningful text
            if not text.strip():
                continue

            # Simple sentiment analysis (would use LLM in production)
            sentiment = self._simple_sentiment_analysis(text)
            sentiments.append(sentiment)

            # Check if recent
            published_str = article.get("published_at", "")
            if published_str:
                try:
                    pub_date = datetime.strptime(published_str.split('T')[0], '%Y-%m-%d')
                    if pub_date >= recent_cutoff:
                        recent_count += 1
                except:
                    pass

            # Identify catalysts
            catalyst = self._identify_catalyst(text, article)
            if catalyst:
                catalysts.append(catalyst)

            # Extract entities (company names, products)
            entities = self._extract_entities(text)
            key_entities.update(entities)

            # Identify risk events
            if self._is_risk_event(text):
                risk_events.append({
                    "type": "negative_news",
                    "title": title[:100],
                    "sentiment": sentiment,
                })

        # Calculate overall sentiment
        overall_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

        # Build analysis
        analysis = NewsAnalysis(
            ticker=ticker,
            overall_sentiment=overall_sentiment,
            sentiment_breakdown={
                "positive": sum(1 for s in sentiments if s > 0.1),
                "neutral": sum(1 for s in sentiments if -0.1 <= s <= 0.1),
                "negative": sum(1 for s in sentiments if s < -0.1),
            },
            news_volume=len(news_articles),
            recent_news_count=recent_count,
            catalysts=catalysts[:10],  # Limit to top 10
            key_events=self._summarize_events(catalysts)[:5],
            risk_events=risk_events[:5],
            key_entities=list(key_entities)[:10],
            summary=self._generate_news_summary(overall_sentiment, catalysts, risk_events),
            confidence=min(1.0, len(news_articles) / 20) if news_articles else 0.3,
        )

        return analysis

    def _simple_sentiment_analysis(self, text: str) -> float:
        """
        Simple rule-based sentiment analysis.

        In production, this would use an LLM or dedicated sentiment service.
        Returns score from -1 (very negative) to +1 (very positive).
        """
        positive_words = [
            'gain', 'gains', 'positive', 'up', 'rise', 'rising', 'rose',
            'bullish', 'growth', 'profit', 'profits', 'earnings', 'beat',
            'exceeds', 'strong', 'strength', 'success', 'successful',
            'launch', 'announces', 'partnership', 'deal', 'agreement',
            'upgrade', 'buy', 'recommend', 'target', 'opportunity',
            'innovation', 'breakthrough', 'patent', 'approval'
        ]

        negative_words = [
            'loss', 'losses', 'negative', 'down', 'fall', 'falling', 'fell',
            'bearish', 'decline', 'drop', 'plunge', 'crash',
            'miss', 'misses', 'weak', 'weakness', 'failure', 'failed',
            'recall', 'warning', 'concern', 'investigation', 'scandal',
            'downgrade', 'sell', 'cut', 'reduce', 'layoff',
            'lawsuit', 'regulation', 'penalty', 'fine', 'ban'
        ]

        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        total = pos_count + neg_count
        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total

    def _identify_catalyst(self, text: str, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Identify if article contains a market catalyst."""
        catalyst_keywords = {
            'earnings': ['earnings', 'eps', 'revenue', 'guidance'],
            'product': ['product', 'launch', 'release', 'announcement'],
            'm&a': ['acquisition', 'acquire', 'merger', 'deal'],
            'partnership': ['partnership', 'collaboration', 'agreement'],
            'regulation': ['fda', 'approval', 'reject', 'regulation'],
            'legal': ['lawsuit', 'settlement', 'court', 'judge'],
            'management': ['ceo', 'executive', 'appointment', 'resign'],
            'financial': ['dividend', 'buyback', 'debt', 'financing'],
        }

        text_lower = text.lower()

        for catalyst_type, keywords in catalyst_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return {
                    "type": catalyst_type,
                    "title": article.get("title", "")[:100],
                    "source": article.get("source", ""),
                    "published_at": article.get("published_at", ""),
                }

        return None

    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities (simplified - would use NER in production)."""
        # Look for capitalized words that might be proper nouns
        import re
        # Simple pattern: capitalized words (but not sentence starts)
        # This is a very simplified approach
        entities = set()

        # Add ticker symbol if mentioned
        # For production, use spaCy or similar NER
        return list(entities)

    def _is_risk_event(self, text: str) -> bool:
        """Check if text describes a risk event."""
        risk_indicators = [
            'investigation', 'lawsuit', 'recall', 'scandal', 'fraud',
            'regulatory', 'penalty', 'fine', 'ban', 'restructuring',
            'layoff', 'downgrade', 'debt', 'default', 'bankruptcy'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in risk_indicators)

    def _summarize_events(self, catalysts: List[Dict[str, Any]]) -> List[str]:
        """Create brief summaries of key events."""
        summaries = []
        for cat in catalysts[:5]:
            summaries.append(f"{cat['type'].upper()}: {cat['title']}")
        return summaries

    def _generate_news_summary(
        self,
        sentiment: float,
        catalysts: List[Dict[str, Any]],
        risk_events: List[Dict[str, Any]]
    ) -> str:
        """Generate narrative summary of news analysis."""
        parts = []

        # Sentiment description
        if sentiment > 0.3:
            parts.append("News sentiment is predominantly positive.")
        elif sentiment < -0.3:
            parts.append("News sentiment is predominantly negative.")
        else:
            parts.append("News sentiment is neutral to mixed.")

        # Catalysts
        if catalysts:
            catalyst_types = [c['type'] for c in catalysts[:5]]
            parts.append(f"Identified {len(catalysts)} catalysts including {', '.join(set(catalyst_types[:3]))}.")

        # Risk events
        if risk_events:
            parts.append(f"Detected {len(risk_events)} potential risk events.")

        return " ".join(parts)


class FundamentalsAnalystNode(BaseNode):
    """
    Fundamental analysis agent that evaluates financial health and valuation.

    Analyzes financial statements, key ratios, and company fundamentals
    to determine intrinsic value and financial stability.
    """

    def __init__(self):
        super().__init__("fundamentals_analyst_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Perform fundamental analysis on all tickers with financial data."""
        self.log(f"Performing fundamental analysis")

        for ticker, ticker_data in state.ticker_data.items():
            if not ticker_data.financial_statements and not ticker_data.key_metrics:
                self.log(f"Skipping {ticker}: no fundamental data", "WARNING")
                continue

            try:
                self.log(f"Analyzing fundamentals for {ticker}")
                analysis = await self._analyze_fundamentals(ticker, ticker_data)
                state.fundamental_analyses[ticker] = analysis
                self.log(f"Fundamental analysis for {ticker}: {analysis.valuation} (PE: {analysis.pe_ratio:.1f})")
            except Exception as e:
                self.log(f"Error in fundamental analysis for {ticker}: {e}", "ERROR")
                state.add_error(self.node_id, str(e), ticker)

        self.log(f"Completed fundamental analysis: {len(state.fundamental_analyses)} tickers")
        return state

    async def _analyze_fundamentals(self, ticker: str, ticker_data: TickerData) -> FundamentalAnalysis:
        """Comprehensive fundamental analysis for a single ticker."""
        # Extract metrics from company info and financial statements
        metrics = ticker_data.key_metrics or {}
        financials = ticker_data.financial_statements or {}

        # Try to get key ratios from various possible keys in OpenBB response
        # OpenBB can return different structures depending on provider
        def get_metric(key_list: List[str], default: Any = None) -> Any:
            """Try multiple possible keys to find a metric."""
            for key in key_list:
                if key in metrics:
                    return metrics[key]
                # Also check nested in financials if needed
                for stmt in financials.values():
                    if isinstance(stmt, dict) and key in stmt:
                        return stmt[key]
            return default

        # Valuation ratios
        pe_ratio = get_metric(['pe_ratio', 'priceEarningsRatio', 'PE Ratio'], None)
        pb_ratio = get_metric(['pb_ratio', 'priceToBookRatio', 'Price to Book'], None)
        ps_ratio = get_metric(['ps_ratio', 'priceToSalesRatio', 'Price to Sales'], None)
        peg_ratio = get_metric(['peg_ratio', 'pegRatio', 'PEG Ratio'], None)

        # Profitability
        roe = get_metric(['roe', 'returnOnEquity', 'ROE'], None)
        roa = get_metric(['roa', 'returnOnAssets', 'ROA'], None)
        net_margin = get_metric(['net_margin', 'netProfitMargin', 'Net Margin'], None)
        operating_margin = get_metric(['operating_margin', 'operatingProfitMargin', 'Operating Margin'], None)

        # Growth
        revenue_growth = get_metric(['revenue_growth', 'revenueGrowth', 'Revenue Growth'], None)
        eps_growth = get_metric(['eps_growth', 'epsGrowth', 'EPS Growth'], None)

        # Financial health
        debt_to_equity = get_metric(['debt_to_equity', 'debtToEquity', 'Debt/Equity'], None)
        current_ratio = get_metric(['current_ratio', 'currentRatio', 'Current Ratio'], None)

        # Free cash flow (try to get from cash flow statement)
        fcf = None
        if 'cashflow' in financials:
            cashflow_df = financials['cashflow']
            # Try to get free cash flow
            if isinstance(cashflow_df, dict):
                # Might be a dict of columns
                fcf = cashflow_df.get('freeCashFlow', cashflow_df.get('Free Cash Flow', None))
                if isinstance(fcf, list) and len(fcf) > 0:
                    fcf = fcf[0]  # Most recent quarter
                elif hasattr(fcf, 'iloc'):
                    try:
                        fcf = fcf.iloc[0]
                    except:
                        pass

        # Valuation assessment
        valuation, fair_value = self._assess_valuation(pe_ratio, pb_ratio, metrics)

        # Strengths and weaknesses
        strengths, weaknesses = self._assess_strengths_weaknesses(
            roe, revenue_growth, debt_to_equity, current_ratio, net_margin
        )

        # Summary
        summary = self._generate_fundamental_summary(
            valuation, pe_ratio, roe, revenue_growth, debt_to_equity, strengths, weaknesses
        )

        # Confidence
        confidence = self._calculate_confidence(
            has_pe=pe_ratio is not None,
            has_financials=bool(financials),
            metrics_count=len([m for m in [pe_ratio, pb_ratio, roe, revenue_growth] if m is not None])
        )

        return FundamentalAnalysis(
            ticker=ticker,
            pe_ratio=float(pe_ratio) if pe_ratio else None,
            pb_ratio=float(pb_ratio) if pb_ratio else None,
            ps_ratio=float(ps_ratio) if ps_ratio else None,
            peg_ratio=float(peg_ratio) if peg_ratio else None,
            roe=float(roe) if roe else None,
            roa=float(roa) if roa else None,
            net_margin=float(net_margin) if net_margin else None,
            operating_margin=float(operating_margin) if operating_margin else None,
            revenue_growth=float(revenue_growth) if revenue_growth else None,
            eps_growth=float(eps_growth) if eps_growth else None,
            debt_to_equity=float(debt_to_equity) if debt_to_equity else None,
            current_ratio=float(current_ratio) if current_ratio else None,
            free_cash_flow=float(fcf) if fcf else None,
            valuation=valuation,
            fair_value_estimate=fair_value,
            strengths=strengths,
            weaknesses=weaknesses,
            summary=summary,
            confidence=confidence,
        )

    def _assess_valuation(
        self,
        pe_ratio: Optional[float],
        pb_ratio: Optional[float],
        metrics: Dict[str, Any]
    ) -> tuple[str, Optional[float]]:
        """Assess whether stock is undervalued, fair, or overvalued."""
        # Simple heuristic based on P/E
        if pe_ratio is None:
            return "fair", None

        # Industry/sector adjusted would be better, but use simple thresholds
        if pe_ratio < 10:
            return "undervalued", None
        elif pe_ratio > 30:
            return "overvalued", None
        else:
            return "fair", None

    def _assess_strengths_weaknesses(
        self,
        roe: Optional[float],
        revenue_growth: Optional[float],
        debt_to_equity: Optional[float],
        current_ratio: Optional[float],
        net_margin: Optional[float]
    ) -> tuple[List[str], List[str]]:
        """Identify key strengths and weaknesses."""
        strengths = []
        weaknesses = []

        if roe and roe > 15:
            strengths.append(f"Strong ROE ({roe:.1f}%)")
        elif roe and roe < 5:
            weaknesses.append(f"Low ROE ({roe:.1f}%)")

        if revenue_growth and revenue_growth > 10:
            strengths.append(f"Revenue growth {revenue_growth:.1f}%")
        elif revenue_growth and revenue_growth < 0:
            weaknesses.append(f"Declining revenue ({revenue_growth:.1f}%)")

        if debt_to_equity and debt_to_equity < 0.5:
            strengths.append(f"Low debt-to-equity ({debt_to_equity:.2f})")
        elif debt_to_equity and debt_to_equity > 2.0:
            weaknesses.append(f"High debt-to-equity ({debt_to_equity:.2f})")

        if current_ratio and current_ratio > 1.5:
            strengths.append(f"Strong liquidity (current ratio {current_ratio:.2f})")
        elif current_ratio and current_ratio < 1.0:
            weaknesses.append(f"Low liquidity (current ratio {current_ratio:.2f})")

        if net_margin and net_margin > 10:
            strengths.append(f"Healthy net margin ({net_margin:.1f}%)")

        return strengths, weaknesses

    def _generate_fundamental_summary(
        self,
        valuation: str,
        pe_ratio: Optional[float],
        roe: Optional[float],
        revenue_growth: Optional[float],
        debt_to_equity: Optional[float],
        strengths: List[str],
        weaknesses: List[str]
    ) -> str:
        """Generate narrative summary."""
        parts = []

        # Valuation statement
        if pe_ratio:
            parts.append(f"P/E ratio of {pe_ratio:.1f} indicates stock is {valuation}.")

        # Profitability
        if roe:
            parts.append(f"ROE of {roe:.1f}% demonstrates {'strong' if roe > 15 else 'moderate' if roe > 10 else 'weak'} profitability.")

        if revenue_growth:
            parts.append(f"Revenue growth of {revenue_growth:.1f}%.")

        # Financial health
        if debt_to_equity:
            parts.append(f"Debt-to-equity of {debt_to_equity:.2f}.")

        # Strengths/weaknesses
        if strengths:
            parts.append(f"Key strengths: {'; '.join(strengths[:2])}.")
        if weaknesses:
            parts.append(f"Key concerns: {'; '.join(weaknesses[:2])}.")

        return " ".join(parts)

    def _calculate_confidence(
        self,
        has_pe: bool,
        has_financials: bool,
        metrics_count: int
    ) -> float:
        """Calculate confidence in fundamental analysis."""
        confidence = 0.3  # Base

        if has_pe:
            confidence += 0.25
        if has_financials:
            confidence += 0.25

        # Based on number of available metrics (max expectation ~8)
        metrics_score = min(metrics_count / 8.0, 1.0) * 0.2
        confidence += metrics_score

        return min(1.0, confidence)


class GrowthAnalystNode(BaseNode):
    """
    Growth analysis agent that evaluates future growth potential.

    Focuses on revenue growth, EPS growth, market opportunity,
    innovation metrics, and management guidance.
    """

    def __init__(self):
        super().__init__("growth_analyst_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Perform growth analysis on all tickers."""
        self.log(f"Performing growth analysis")

        for ticker, ticker_data in state.ticker_data.items():
            try:
                self.log(f"Analyzing growth for {ticker}")
                analysis = await self._analyze_growth(ticker, ticker_data)
                state.growth_analyses[ticker] = analysis
                self.log(f"Growth analysis for {ticker}: score {analysis.growth_score:.1f}/100")
            except Exception as e:
                self.log(f"Error in growth analysis for {ticker}: {e}", "ERROR")
                state.add_error(self.node_id, str(e), ticker)

        self.log(f"Completed growth analysis: {len(state.growth_analyses)} tickers")
        return state

    async def _analyze_growth(self, ticker: str, ticker_data: TickerData) -> GrowthAnalysis:
        """Analyze growth potential for a single ticker."""
        metrics = ticker_data.key_metrics or {}
        financials = ticker_data.financial_statements or {}

        def get_metric(key_list: List[str], default: Any = None) -> Any:
            for key in key_list:
                if key in metrics:
                    return metrics[key]
                for stmt in financials.values():
                    if isinstance(stmt, dict) and key in stmt:
                        return stmt[key]
            return default

        # Extract growth metrics
        revenue_growth = get_metric(['revenue_growth', 'revenueGrowth', 'Revenue Growth'], None)
        eps_growth = get_metric(['eps_growth', 'epsGrowth', 'EPS Growth'], None)

        # Convert to float if present
        if revenue_growth:
            try:
                revenue_growth = float(revenue_growth)
            except:
                revenue_growth = None

        if eps_growth:
            try:
                eps_growth = float(eps_growth)
            except:
                eps_growth = None

        # Calculate CAGR if we have historical data (simplified)
        revenue_cagr = self._estimate_cagr(ticker_data, 'revenue' if 'revenue' in str(financials) else None)

        # Future estimates (would come from analyst estimates endpoint)
        next_quarter_est = get_metric(['next_quarter_est', 'estimatedEarningsAvg', 'Earnings Estimate'], None)
        next_year_est = get_metric(['next_year_est', 'estimatedRevenueAvg', 'Revenue Estimate'], None)
        long_term_growth = get_metric(['long_term_growth', 'longTermGrowth', 'LT Growth'], None)

        # R&D intensity (innovation proxy)
        rd_to_revenue = None
        if 'income' in financials:
            income = financials['income']
            if isinstance(income, dict):
                rd = income.get('research_and_development', income.get('Research And Development', None))
                revenue_val = income.get('revenue', income.get('Total Revenue', None))
                if rd and revenue_val and revenue_val > 0:
                    try:
                        rd_to_revenue = float(rd) / float(revenue_val) * 100
                    except:
                        pass

        # Growth score calculation
        growth_score = self._calculate_growth_score(
            revenue_growth, eps_growth, revenue_cagr, rd_to_revenue, long_term_growth
        )

        # Growth trend
        revenue_trend = self._assess_growth_trend(revenue_growth, revenue_cagr)

        # Summary
        summary = self._generate_growth_summary(
            growth_score, revenue_growth, eps_growth, revenue_trend, rd_to_revenue
        )

        # Confidence
        confidence = self._calculate_growth_confidence(
            has_revenue_growth=revenue_growth is not None,
            has_eps_growth=eps_growth is not None,
            has_estimates=next_year_est is not None
        )

        return GrowthAnalysis(
            ticker=ticker,
            revenue_growth_rate=revenue_growth,
            revenue_growth_trend=revenue_trend,
            eps_growth_rate=eps_growth,
            eps_growth_trend=self._assess_growth_trend(eps_growth, None),
            next_quarter_estimate=float(next_quarter_est) if next_quarter_est else None,
            next_year_estimate=float(next_year_est) if next_year_est else None,
            long_term_growth_rate=float(long_term_growth) if long_term_growth else None,
            rd_to_revenue=rd_to_revenue,
            growth_score=growth_score,
            summary=summary,
            confidence=confidence,
            analyst_type=AnalystType.GROWTH,
        )

    def _estimate_cagr(self, ticker_data: TickerData, metric_name: Optional[str]) -> Optional[float]:
        """Estimate compound annual growth rate from historical data."""
        if not ticker_data.financial_statements:
            return None

        # This would require multi-year financial data which may not be easily accessible
        # For now, return growth rate if available directly
        return None

    def _calculate_growth_score(
        self,
        revenue_growth: Optional[float],
        eps_growth: Optional[float],
        cagr: Optional[float],
        rd_to_revenue: Optional[float],
        long_term_growth: Optional[float]
    ) -> float:
        """Calculate composite growth score (0-100)."""
        score = 50.0  # Base score

        # Revenue growth contribution (up to 30 points)
        if revenue_growth:
            # 20%+ = excellent, 10-20% = good, 5-10% = moderate, <5% = low
            if revenue_growth >= 20:
                score += 30
            elif revenue_growth >= 15:
                score += 25
            elif revenue_growth >= 10:
                score += 20
            elif revenue_growth >= 5:
                score += 10
            else:
                score -= 10

        # EPS growth contribution (up to 25 points)
        if eps_growth:
            if eps_growth >= 25:
                score += 25
            elif eps_growth >= 15:
                score += 20
            elif eps_growth >= 10:
                score += 15
            elif eps_growth >= 5:
                score += 5
            else:
                score -= 15

        # R&D intensity (innovation) - up to 20 points
        if rd_to_revenue:
            if rd_to_revenue > 15:
                score += 20
            elif rd_to_revenue > 10:
                score += 15
            elif rd_to_revenue > 5:
                score += 10

        # Long-term growth estimate (up to 25 points)
        if long_term_growth:
            if long_term_growth >= 15:
                score += 25
            elif long_term_growth >= 10:
                score += 15
            elif long_term_growth >= 5:
                score += 5
            else:
                score -= 10

        return max(0.0, min(100.0, score))

    def _assess_growth_trend(self, current_growth: Optional[float], historical: Optional[float]) -> str:
        """Assess if growth is accelerating, stable, or decelerating."""
        if current_growth is None:
            return "stable"

        # Without historical comparison, assume stable
        if historical is None:
            if current_growth > 15:
                return "accelerating"
            elif current_growth < 0:
                return "declining"
            else:
                return "stable"

        # Compare current to historical
        if current_growth > historical * 1.1:
            return "accelerating"
        elif current_growth < historical * 0.9:
            return "decelerating"
        else:
            return "stable"

    def _generate_growth_summary(
        self,
        score: float,
        revenue_growth: Optional[float],
        eps_growth: Optional[float],
        trend: str,
        rd_to_revenue: Optional[float]
    ) -> str:
        """Generate narrative summary."""
        parts = []

        # Overall growth assessment
        if score >= 70:
            parts.append("Strong growth profile with excellent expansion potential.")
        elif score >= 50:
            parts.append("Moderate growth prospects with steady expansion.")
        elif score >= 30:
            parts.append("Limited growth potential with some constraints.")
        else:
            parts.append("Weak growth outlook with significant headwinds.")

        # Specific metrics
        if revenue_growth:
            parts.append(f"Revenue growth at {revenue_growth:.1f}% shows {'strong' if revenue_growth > 10 else 'moderate' if revenue_growth > 0 else 'declining'} performance.")

        if eps_growth:
            parts.append(f"EPS growth of {eps_growth:.1f}% indicates {'robust' if eps_growth > 15 else 'positive' if eps_growth > 0 else 'weak'} earnings momentum.")

        if rd_to_revenue:
            parts.append(f"R&D investment at {rd_to_revenue:.1f}% of revenue supports future innovation.")

        parts.append(f"Growth trend is {trend}.")

        return " ".join(parts)

    def _calculate_growth_confidence(
        self,
        has_revenue_growth: bool,
        has_eps_growth: bool,
        has_estimates: bool
    ) -> float:
        """Calculate confidence in growth analysis."""
        confidence = 0.3

        if has_revenue_growth:
            confidence += 0.3
        if has_eps_growth:
            confidence += 0.2
        if has_estimates:
            confidence += 0.2

        return min(1.0, confidence)


class RiskAnalystNode(BaseNode):
    """
    Risk analysis agent that evaluates various risk factors.

    Analyzes volatility, drawdown, financial risk, liquidity risk,
    and portfolio-level considerations.
    """

    def __init__(self):
        super().__init__("risk_analyst_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Perform risk analysis on all tickers."""
        self.log(f"Performing risk analysis")

        for ticker, ticker_data in state.ticker_data.items():
            try:
                self.log(f"Analyzing risk for {ticker}")
                analysis = await self._analyze_risk(ticker, ticker_data, state)
                state.risk_analyses[ticker] = analysis
                self.log(f"Risk analysis for {ticker}: score {analysis.risk_score:.1f}/100 ({analysis.risk_level})")
            except Exception as e:
                self.log(f"Error in risk analysis for {ticker}: {e}", "ERROR")
                state.add_error(self.node_id, str(e), ticker)

        self.log(f"Completed risk analysis: {len(state.risk_analyses)} tickers")
        return state

    async def _analyze_risk(self, ticker: str, ticker_data: TickerData, state: DeerflowState) -> RiskAnalysis:
        """Comprehensive risk analysis."""
        # Get returns for volatility and VaR calculations
        returns = self._calculate_returns(ticker_data.historical_data)

        # Volatility
        volatility = self._calculate_volatility(returns) if len(returns) > 0 else 0.0

        # VaR and CVaR
        var_95, cvar_95 = self._calculate_var_cvar(returns, 0.05)

        # Drawdown analysis
        max_drawdown, current_drawdown = self._calculate_drawdowns(ticker_data.historical_data)

        # Get ticker's beta from market data (would need market index, simplified)
        beta = self._estimate_beta(returns)

        # Financial risk metrics
        metrics = ticker_data.key_metrics or {}
        financials = ticker_data.financial_statements or {}

        def get_metric(key_list: List[str]) -> Optional[float]:
            for key in key_list:
                if key in metrics:
                    try:
                        return float(metrics[key])
                    except:
                        pass
            return None

        debt_to_equity = get_metric(['debt_to_equity', 'debtToEquity', 'Debt/Equity'])
        interest_coverage = get_metric(['interest_coverage', 'interestCoverage', 'Interest Coverage'])
        current_ratio = get_metric(['current_ratio', 'currentRatio', 'Current Ratio'])

        # Liquidity from market data
        avg_volume = self._estimate_avg_volume(ticker_data.historical_data)
        bid_ask_spread = None  # Would need real-time data

        # Calculate composite risk score
        risk_score = self._calculate_risk_score(
            volatility, max_drawdown, debt_to_equity, current_ratio, beta
        )

        # Risk level classification
        if risk_score < 30:
            risk_level = "low"
        elif risk_score < 60:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Summary
        summary = self._generate_risk_summary(
            volatility, max_drawdown, beta, debt_to_equity, risk_level
        )

        # Confidence
        confidence = self._calculate_risk_confidence(
            returns_available=len(returns) > 0,
            has_financials=bool(financials),
            volatility_calculated=volatility > 0
        )

        return RiskAnalysis(
            ticker=ticker,
            beta=beta,
            volatility=volatility,
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            average_volume=avg_volume,
            debt_to_equity=debt_to_equity,
            interest_coverage=interest_coverage,
            working_capital_ratio=current_ratio,
            risk_score=risk_score,
            risk_level=risk_level,
            summary=summary,
            confidence=confidence,
            analyst_type=AnalystType.RISK,
        )

    def _calculate_returns(self, historical_data: Dict[str, List[Any]]) -> List[float]:
        """Calculate daily returns from close prices."""
        if 'close' not in historical_data:
            return []

        closes = historical_data['close']
        if len(closes) < 2:
            return []

        returns = []
        for i in range(1, len(closes)):
            try:
                prev = float(closes[i-1])
                curr = float(closes[i])
                if prev > 0:
                    ret = (curr - prev) / prev
                    returns.append(ret)
            except:
                continue

        return returns

    def _calculate_volatility(self, returns: List[float], annualize: bool = True) -> float:
        """Calculate annualized volatility from daily returns."""
        if len(returns) < 20:
            return 0.0

        import numpy as np
        daily_vol = np.std(returns, ddof=1)

        if annualize:
            # 252 trading days per year
            return float(daily_vol * np.sqrt(252))
        return float(daily_vol)

    def _calculate_var_cvar(self, returns: List[float], alpha: float = 0.05) -> tuple[Optional[float], Optional[float]]:
        """Calculate Value at Risk and Conditional VaR."""
        if len(returns) < 30:
            return None, None

        import numpy as np

        # Sort returns
        sorted_returns = sorted(returns)

        # Index for VaR
        var_index = int(len(sorted_returns) * alpha)
        var_95 = -sorted_returns[var_index]  # Negative returns become positive VaR

        # CVaR: average of returns worse than VaR
        cvar_returns = sorted_returns[:var_index]
        if cvar_returns:
            cvar_95 = -sum(cvar_returns) / len(cvar_returns)
        else:
            cvar_95 = var_95

        return float(var_95), float(cvar_95)

    def _calculate_drawdowns(self, historical_data: Dict[str, List[Any]]) -> tuple[Optional[float], Optional[float]]:
        """Calculate maximum and current drawdowns."""
        if 'close' not in historical_data:
            return None, None

        closes = [float(c) for c in historical_data['close'] if c is not None]
        if len(closes) < 2:
            return None, None

        # Calculate running maximum
        running_max = np.maximum.accumulate(closes)
        drawdown = (closes - running_max) / running_max

        max_drawdown = float(np.min(drawdown)) * 100  # As percentage
        current_drawdown = float(drawdown[-1]) * 100 if drawdown[-1] < 0 else 0.0

        return max_drawdown, current_drawdown

    def _estimate_beta(self, returns: List[float]) -> Optional[float]:
        """
        Estimate beta relative to market.
        
        In production, would fetch market index returns (SPY, etc.)
        For now, use a simplified estimate based on volatility
        """
        if len(returns) < 60:
            return 1.0  # Default to market beta

        vol = self._calculate_volatility(returns, annualize=False)
        # Very rough approximation: beta ~= stock volatility / market volatility
        # Market volatility typically ~1.2% daily
        market_daily_vol = 0.012
        estimated_beta = vol / market_daily_vol if market_daily_vol > 0 else 1.0

        return max(0.0, min(3.0, estimated_beta))  # Clamp to reasonable range

    def _estimate_avg_volume(self, historical_data: Dict[str, List[Any]]) -> Optional[float]:
        """Estimate average daily volume."""
        if 'volume' not in historical_data:
            return None

        volumes = [float(v) for v in historical_data['volume'] if v is not None]
        if not volumes:
            return None

        return float(sum(volumes) / len(volumes))

    def _calculate_risk_score(
        self,
        volatility: float,
        max_drawdown: Optional[float],
        debt_to_equity: Optional[float],
        current_ratio: Optional[float],
        beta: Optional[float]
    ) -> float:
        """
        Calculate composite risk score (0-100, higher = riskier).
        
        Components:
        - Volatility (annualized): 25 points
        - Max drawdown: 25 points
        - Financial leverage: 25 points
        - Beta: 25 points
        """
        score = 0.0

        # 1. Volatility (0-25 points)
        # < 15% = low risk (5), 15-25% = medium (15), > 25% = high (25)
        if volatility < 0.15:
            score += 5
        elif volatility < 0.25:
            score += 15
        else:
            score += 25

        # 2. Max drawdown (0-25 points)
        if max_drawdown:
            if max_drawdown < 20:  # Less than 20% max drawdown
                score += 5
            elif max_drawdown < 40:
                score += 15
            else:
                score += 25

        # 3. Financial leverage (0-25 points)
        if debt_to_equity:
            if debt_to_equity < 0.5:
                score += 5
            elif debt_to_equity < 1.5:
                score += 15
            else:
                score += 25
        else:
            score += 10  # Neutral if unknown

        # 4. Beta (0-25 points)
        if beta:
            if beta < 0.8:
                score += 5
            elif beta < 1.2:
                score += 15
            else:
                score += 25
        else:
            score += 10  # Neutral if unknown

        return min(100.0, score)

    def _generate_risk_summary(
        self,
        volatility: float,
        max_drawdown: Optional[float],
        beta: Optional[float],
        debt_to_equity: Optional[float],
        risk_level: str
    ) -> str:
        """Generate narrative summary."""
        parts = []

        parts.append(f"Overall risk profile is {risk_level}. ")

        if volatility > 0:
            parts.append(f"Annualized volatility is {volatility:.1%}. ")

        if max_drawdown:
            parts.append(f"Maximum historical drawdown: {max_drawdown:.1f}%. ")

        if beta:
            parts.append(f"Beta of {beta:.2f} indicates {'higher' if beta > 1.2 else 'lower' if beta < 0.8 else 'market'} systematic risk. ")

        if debt_to_equity:
            parts.append(f"Debt-to-equity of {debt_to_equity:.2f} suggests {'high' if debt_to_equity > 1.5 else 'moderate' if debt_to_equity > 0.5 else 'low'} financial leverage.")

        return " ".join(parts)

    def _calculate_risk_confidence(
        self,
        returns_available: bool,
        has_financials: bool,
        volatility_calculated: bool
    ) -> float:
        """Calculate confidence in risk analysis."""
        confidence = 0.3

        if returns_available:
            confidence += 0.4
        if volatility_calculated:
            confidence += 0.2
        if has_financials:
            confidence += 0.1

        return min(1.0, confidence)


class ConsensusNode(BaseNode):
    """
    Consensus aggregation node that combines all analyst signals.

    Weights and synthesizes signals from all analyst types to produce
    a unified trading signal with comprehensive justification.
    """

    def __init__(self):
        super().__init__("consensus_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Generate consensus signals for all tickers with complete analysis."""
        self.log(f"Generating consensus signals")

        # Weights for each analyst type (configurable)
        weights = {
            AnalystType.TECHNICAL: 0.20,
            AnalystType.FUNDAMENTALS: 0.25,
            AnalystType.NEWS: 0.15,
            AnalystType.GROWTH: 0.15,
            AnalystType.RISK: -0.15,  # Negative weight - higher risk reduces signal
            AnalystType.MACRO: 0.10,
        }

        for ticker in state.tickers:
            # Check which analyses we have
            analyses = {}
            if ticker in state.technical_analyses:
                analyses[AnalystType.TECHNICAL] = state.technical_analyses[ticker]
            if ticker in state.fundamental_analyses:
                analyses[AnalystType.FUNDAMENTALS] = state.fundamental_analyses[ticker]
            if ticker in state.news_analyses:
                analyses[AnalystType.NEWS] = state.news_analyses[ticker]
            if ticker in state.growth_analyses:
                analyses[AnalystType.GROWTH] = state.growth_analyses[ticker]
            if ticker in state.risk_analyses:
                analyses[AnalystType.RISK] = state.risk_analyses[ticker]
            if ticker in state.macro_analyses:
                analyses[AnalystType.MACRO] = state.macro_analyses[ticker]

            if not analyses:
                self.log(f"Skipping {ticker}: no analysis data", "WARNING")
                continue

            try:
                self.log(f"Generating consensus for {ticker} from {len(analyses)} analysts")
                consensus = await self._generate_consensus(ticker, analyses, weights)
                state.consensus_signals[ticker] = consensus
                self.log(f"Consensus for {ticker}: {consensus.overall_signal} (strength: {consensus.signal_strength:.2f})")
            except Exception as e:
                self.log(f"Error generating consensus for {ticker}: {e}", "ERROR")
                state.add_error(self.node_id, str(e), ticker)

        self.log(f"Completed consensus generation: {len(state.consensus_signals)} tickers")
        return state

    async def _generate_consensus(
        self,
        ticker: str,
        analyses: Dict[AnalystType, Any],
        weights: Dict[AnalystType, float]
    ) -> ConsensusSignal:
        """Generate consensus signal from all analyst outputs."""
        weighted_scores = []
        analyst_signals = {}

        for analyst_type, analysis in analyses.items():
            weight = weights.get(analyst_type, 0.0)

            # Convert analysis to a score (-1 to +1)
            score = self._convert_to_score(analysis, analyst_type)

            # Apply weight
            weighted_score = score * abs(weight) * (1 if weight >= 0 else -1)
            weighted_scores.append(weighted_score)

            # Store for tracking
            analyst_signals[analyst_type] = {
                "score": float(score),
                "weight": float(weight),
                "weighted_score": float(weighted_score),
                "confidence": float(analysis.confidence) if hasattr(analysis, 'confidence') else 0.5,
            }

        # Sum weighted scores
        total_weighted_score = sum(weighted_scores)

        # Normalize by sum of absolute weights of analyses we actually have
        active_weights = sum(abs(weights.get(at, 0)) for at in analyses.keys())
        if active_weights > 0:
            normalized_score = total_weighted_score / active_weights
        else:
            normalized_score = 0.0

        # Convert to signal type
        overall_signal, signal_strength = self._score_to_signal(normalized_score)

        # Calculate consensus confidence as weighted average of individual confidences
        confidences = [a.confidence for a in analyses.values() if hasattr(a, 'confidence')]
        if confidences:
            consensus_confidence = sum(confidences) / len(confidences)
        else:
            consensus_confidence = 0.5

        # Estimate target price (simplified - would need more data)
        target_price = None
        if AnalystType.FUNDAMENTALS in analyses:
            fund_analysis = analyses[AnalystType.FUNDAMENTALS]
            if hasattr(fund_analysis, 'fair_value_estimate') and fund_analysis.fair_value_estimate:
                target_price = fund_analysis.fair_value_estimate

        # Generate consensus rationale
        rationale = self._generate_consensus_rationale(analyst_signals, overall_signal, signal_strength)

        return ConsensusSignal(
            ticker=ticker,
            overall_signal=overall_signal,
            signal_strength=signal_strength,
            analyst_signals=analyst_signals,
            technical_weight=weights.get(AnalystType.TECHNICAL, 0),
            fundamental_weight=weights.get(AnalystType.FUNDAMENTALS, 0),
            news_weight=weights.get(AnalystType.NEWS, 0),
            growth_weight=weights.get(AnalystType.GROWTH, 0),
            risk_weight=weights.get(AnalystType.RISK, 0),
            macro_weight=weights.get(AnalystType.MACRO, 0),
            consensus_confidence=consensus_confidence,
            target_price=target_price,
        )

    def _convert_to_score(self, analysis: Any, analyst_type: AnalystType) -> float:
        """
        Convert an analysis result to a normalized score (-1 to +1).
        
        -1 = strongly bearish/sell
        0 = neutral/hold
        +1 = strongly bullish/buy
        """
        if analyst_type == AnalystType.TECHNICAL:
            # Technical: Use trend and signals
            trend_score = 0.0
            if analysis.trend == "bullish":
                trend_score = 0.5
            elif analysis.trend == "bearish":
                trend_score = -0.5

            momentum_score = 0.0
            if analysis.momentum == "oversold":
                momentum_score = 0.3  # Can bounce
            elif analysis.momentum == "overbought":
                momentum_score = -0.3  # May correct

            # Signal contribution
            signal_strength = 0.0
            if analysis.signals:
                buy_strength = sum(s['strength'] for s in analysis.signals if s['signal'] == 'buy')
                sell_strength = sum(s['strength'] for s in analysis.signals if s['signal'] == 'sell')
                signal_strength = (buy_strength - sell_strength) / max(1.0, len(analysis.signals))

            return trend_score + momentum_score + signal_strength * 0.5

        elif analyst_type == AnalystType.FUNDAMENTALS:
            # Fundamentals: Use valuation and key metrics
            score = 0.0

            if analysis.valuation == "undervalued":
                score += 0.6
            elif analysis.valuation == "overvalued":
                score -= 0.6

            # Add small contribution from ROE if available
            if analysis.roe:
                if analysis.roe > 15:
                    score += 0.2
                elif analysis.roe < 5:
                    score -= 0.2

            # Revenue growth
            if analysis.revenue_growth:
                if analysis.revenue_growth > 10:
                    score += 0.2
                elif analysis.revenue_growth < 0:
                    score -= 0.2

            return max(-1.0, min(1.0, score))

        elif analyst_type == AnalystType.NEWS:
            # News: Sentiment score directly maps (-1 to +1)
            return analysis.overall_sentiment

        elif analyst_type == AnalystType.GROWTH:
            # Growth: Convert growth score to signal
            # 0-100 scale -> -1 to +1
            # 50 is neutral, 100 is strongly bullish, 0 is strongly bearish
            normalized = (analysis.growth_score - 50) / 50.0
            return max(-1.0, min(1.0, normalized))

        elif analyst_type == AnalystType.RISK:
            # Risk: Negative weight already applied in weights
            # Convert risk score to additional penalty/bonus
            # High risk (80+) = -0.3, Low risk (<30) = +0.2
            if analysis.risk_score > 70:
                return -0.3
            elif analysis.risk_score < 30:
                return 0.2
            else:
                return 0.0

        elif analyst_type == AnalystType.MACRO:
            # Macro: macro_score 0-100 -> -1 to +1
            normalized = (analysis.macro_score - 50) / 50.0
            return max(-1.0, min(1.0, normalized))

        return 0.0

    def _score_to_signal(self, score: float) -> tuple[SignalType, float]:
        """Convert normalized score to signal type and strength."""
        abs_score = abs(score)

        if abs_score < 0.2:
            signal_type = SignalType.HOLD
            strength = abs_score / 0.2 if abs_score > 0 else 0.0
        elif abs_score < 0.5:
            signal_type = SignalType.BUY if score > 0 else SignalType.SELL
            strength = (abs_score - 0.2) / 0.3
        elif abs_score < 0.8:
            signal_type = SignalType.STRONG_BUY if score > 0 else SignalType.STRONG_SELL
            strength = (abs_score - 0.5) / 0.3
        else:
            signal_type = SignalType.STRONG_BUY if score > 0 else SignalType.STRONG_SELL
            strength = 1.0

        return signal_type, strength

    def _generate_consensus_rationale(
        self,
        analyst_signals: Dict[AnalystType, Dict[str, Any]],
        overall_signal: SignalType,
        strength: float
    ) -> str:
        """Generate rationale explaining consensus."""
        parts = []

        # Overall recommendation
        if overall_signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            parts.append("Based on综合分析，多数分析师给出买入建议。")
        elif overall_signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            parts.append("基于综合分析，多数分析师建议卖出。")
        else:
            parts.append("综合分析显示信号中性，建议持有。")

        # Analyst breakdown
        bullish_analysts = sum(1 for s in analyst_signals.values() if s['score'] > 0.2)
        bearish_analysts = sum(1 for s in analyst_signals.values() if s['score'] < -0.2)
        neutral_analysts = len(analyst_signals) - bullish_analysts - bearish_analysts

        parts.append(f"分析师意见：看多{bullish_analysts}位，看空{bearish_analysts}位，中性{neutral_analysts}位。")

        # Key contributors
        positive_contributors = [
            at.value for at, s in analyst_signals.items()
            if s['score'] > 0.3
        ]
        negative_contributors = [
            at.value for at, s in analyst_signals.items()
            if s['score'] < -0.3
        ]

        if positive_contributors:
            parts.append(f"看多因素：{', '.join(positive_contributors)}。")
        if negative_contributors:
            parts.append(f"看空因素：{', '.join(negative_contributors)}。")

        return " ".join(parts[:4])  # Limit to 4 sentences


class DecisionNode(BaseNode):
    """
    Final decision node that synthesizes consensus signal into trading decision.

    In Phase 2+, uses consensus from all analysts rather than just technical.
    """

    def __init__(self):
        super().__init__("decision_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Generate trading decisions for all analyzed tickers."""
        self.log(f"Generating final trading decisions")

        for ticker in state.tickers:
            if ticker not in state.consensus_signals:
                # Fallback: if no consensus, try technical only
                if ticker in state.technical_analyses:
                    self.log(f"No consensus for {ticker}, using technical only", "WARNING")
                    decision = await self._make_fallback_decision(ticker, state)
                    state.trading_decisions[ticker] = decision
                else:
                    self.log(f"Skipping {ticker}: no analysis data", "WARNING")
                continue

            try:
                self.log(f"Processing decision for {ticker}")
                decision = await self._make_decision(ticker, state)
                state.trading_decisions[ticker] = decision
                self.log(f"Decision for {ticker}: {decision.action.value.upper()} - {decision.position_size:.1f}%")
            except Exception as e:
                self.log(f"Error generating decision for {ticker}: {e}", "ERROR")
                state.add_error(self.node_id, str(e), ticker)

        self.log(f"Completed decisions: {len(state.trading_decisions)}/{len(state.tickers)}")
        return state

    async def _make_decision(self, ticker: str, state: DeerflowState) -> TradingDecision:
        """Generate trading decision using consensus signal."""
        consensus = state.consensus_signals[ticker]
        tech_analysis = state.technical_analyses.get(ticker)
        risk_analysis = state.risk_analyses.get(ticker)

        # Base decision on consensus signal
        signal_strength = consensus.signal_strength
        overall_signal = consensus.overall_signal

        # Determine action
        if overall_signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            action = SignalType.BUY if signal_strength > 0.6 else SignalType.HOLD
        elif overall_signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            action = SignalType.SELL if signal_strength > 0.6 else SignalType.HOLD
        else:
            action = SignalType.HOLD

        # Position sizing based on consensus confidence and signal strength
        base_position = self.settings.max_position_size

        if action == SignalType.BUY:
            # Adjust by confidence and signal strength
            position_size = base_position * consensus.consensus_confidence * signal_strength
        elif action == SignalType.SELL:
            position_size = -min(base_position * 0.5, 10.0)  # Max 10% short or half position
        else:
            position_size = 0.0

        # Risk management: Use risk analysis for stops
        stop_loss = None
        take_profit = None
        risk_reward_ratio = None

        if action == SignalType.BUY and risk_analysis and risk_analysis.volatility > 0:
            # ATR-based stops if available, otherwise volatility-based
            if tech_analysis and 'ATR_14' in tech_analysis.indicators:
                atr_value = tech_analysis.indicators['ATR_14'][-1]
                # Get current price
                current_price = self._get_current_price(state.ticker_data[ticker])
                if current_price:
                    stop_loss = current_price - 2 * atr_value
                    take_profit = current_price + 4 * atr_value
                    risk_reward_ratio = 4.0 / 2.0  # 2:1

        # Generate rationale using consensus rationale + technical details
        rationale = self._generate_rationale(consensus, tech_analysis, risk_analysis, action)

        return TradingDecision(
            ticker=ticker,
            action=action,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward_ratio,
            rationale=rationale,
            confidence=consensus.consensus_confidence,
        )

    async def _make_fallback_decision(self, ticker: str, state: DeerflowState) -> TradingDecision:
        """Fallback decision using only technical analysis when consensus is missing."""
        # Reuse old Phase 1 logic
        tech_analysis = state.technical_analyses[ticker]

        signals = tech_analysis.signals
        trend = tech_analysis.trend
        confidence = tech_analysis.confidence

        buy_strength = sum(s['strength'] * (1 if s['signal'] == 'buy' else 0) for s in signals)
        sell_strength = sum(s['strength'] * (1 if s['signal'] == 'sell' else 0) for s in signals)
        net_signal = buy_strength - sell_strength

        if net_signal > 1.5 and trend == "bullish" and confidence > 0.6:
            action = SignalType.BUY
        elif net_signal < -1.5 and trend == "bearish" and confidence > 0.6:
            action = SignalType.SELL
        else:
            action = SignalType.HOLD

        position_size = 0.0
        if action == SignalType.BUY:
            signal_strength = min(1.0, net_signal / 3.0)
            position_size = self.settings.max_position_size * confidence * signal_strength
        elif action == SignalType.SELL:
            position_size = -10.0

        rationale = self._generate_fallback_rationale(tech_analysis, action, net_signal)

        return TradingDecision(
            ticker=ticker,
            action=action,
            position_size=position_size,
            rationale=rationale,
            confidence=confidence,
        )

    def _get_current_price(self, ticker_data: TickerData) -> Optional[float]:
        """Extract current price from ticker data."""
        if 'close' in ticker_data.historical_data:
            closes = ticker_data.historical_data['close']
            if closes and len(closes) > 0:
                try:
                    return float(closes[-1])
                except:
                    pass
        return None

    def _generate_rationale(
        self,
        consensus: ConsensusSignal,
        tech_analysis: Optional[TechnicalAnalysis],
        risk_analysis: Optional[RiskAnalysis],
        action: SignalType
    ) -> str:
        """Generate comprehensive rationale using all analysts."""
        parts = []

        # Consensus summary
        signal_desc = "买入" if consensus.overall_signal.value in ['buy', 'strong_buy'] else \
                     "卖出" if consensus.overall_signal.value in ['sell', 'strong_sell'] else \
                     "持有"
        parts.append(f"综合分析给出{signal_desc}建议，强度{consensus.signal_strength:.0%}，可信度{consensus.consensus_confidence:.0%}。")

        # Analyst breakdown
        if consensus.analyst_signals:
            parts.append("分析师意见：")
            for at, sig in consensus.analyst_signals.items():
                contribution = "看多" if sig['score'] > 0.2 else "看空" if sig['score'] < -0.2 else "中性"
                parts.append(f"{at.value} {contribution}；")

        # Technical context
        if tech_analysis:
            parts.append(f"技术面：{tech_analysis.trend}趋势，{tech_analysis.momentum}动量。")

        # Risk context
        if risk_analysis:
            parts.append(f"风险等级：{risk_analysis.risk_level}（波动率{risk_analysis.volatility:.1%}）。")

        # Target price if available
        if consensus.target_price:
            parts.append(f"目标价${consensus.target_price:.2f}。")

        # Final reasoning
        if action == SignalType.BUY:
            if consensus.signal_strength > 0.7:
                parts.append("强烈推荐买入。")
            else:
                parts.append("建议小仓位买入。")
        elif action == SignalType.SELL:
            parts.append("建议卖出或减仓。")
        else:
            parts.append("暂无明确信号，建议观望。")

        return " ".join(parts[:5])  # Limit length

    def _generate_fallback_rationale(
        self,
        tech_analysis: TechnicalAnalysis,
        action: SignalType,
        net_signal: float
    ) -> str:
        """Generate rationale for fallback (technical-only) decision."""
        parts = [
            f"技术分析：{tech_analysis.trend}趋势，{tech_analysis.momentum}动量。",
            f"信号强度{net_signal:.2f}。",
            f"可信度{tech_analysis.confidence:.1%}。",
        ]

        if action == SignalType.BUY:
            parts.append("技术指标偏向多头，建议买入。")
        elif action == SignalType.SELL:
            parts.append("技术指标偏向空头，建议卖出。")
        else:
            parts.append("技术信号不明确，建议持有观望。")

        return " ".join(parts)
