"""
Analyst nodes for fundamental and technical analysis.

Includes: TechnicalAnalystNode, NewsAnalystNode, FundamentalsAnalystNode, GrowthAnalystNode, RiskAnalystNode
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np

from ..models import (
    DeerflowState, TickerData, TechnicalAnalysis, AnalystType, SignalType,
    NewsAnalysis, FundamentalAnalysis, GrowthAnalysis, RiskAnalysis, MacroAnalysis,
)
from .base import BaseNode


class TechnicalAnalystNode(BaseNode):
    """Technical analysis agent that analyzes price patterns and indicators."""

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
        df = self._dict_to_dataframe(ticker_data.historical_data)

        if df.empty:
            raise ValueError(f"No price data available for {ticker}")

        indicators = self._calculate_indicators(df)
        signals = self._generate_signals(df, indicators)
        support_levels, resistance_levels = self._find_support_resistance(df)
        trend, trend_strength = self._determine_trend(df)
        momentum, rsi = self._calculate_momentum(df)
        volatility = self._calculate_volatility(df)
        summary = self._generate_summary(trend, momentum, signals, support_levels, resistance_levels)
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

        indicators['SMA_20'] = close.rolling(20).mean().tolist()
        indicators['SMA_50'] = close.rolling(50).mean().tolist()
        indicators['SMA_200'] = close.rolling(200).mean().tolist()
        indicators['EMA_12'] = close.ewm(span=12, adjust=False).mean().tolist()
        indicators['EMA_26'] = close.ewm(span=26, adjust=False).mean().tolist()
        indicators['RSI_14'] = self._calculate_rsi(close).tolist()

        macd_line = (pd.Series(indicators['EMA_12']) - pd.Series(indicators['EMA_26'])).tolist()
        signal_line = pd.Series(macd_line).ewm(span=9, adjust=False).mean().tolist()
        indicators['MACD'] = macd_line
        indicators['MACD_SIGNAL'] = signal_line
        indicators['MACD_HIST'] = (pd.Series(macd_line) - pd.Series(signal_line)).tolist()

        sma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        indicators['BB_UPPER'] = (sma_20 + 2 * std_20).tolist()
        indicators['BB_MIDDLE'] = sma_20.tolist()
        indicators['BB_LOWER'] = (sma_20 - 2 * std_20).tolist()

        indicators['ATR_14'] = self._calculate_atr(high, low, close).tolist()
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

        sma_20 = pd.Series(indicators.get('SMA_20', []))
        sma_50 = pd.Series(indicators.get('SMA_50', []))
        sma_200 = pd.Series(indicators.get('SMA_200', []))
        rsi = pd.Series(indicators.get('RSI_14', []))
        macd_line = pd.Series(indicators.get('MACD', []))
        macd_signal = pd.Series(indicators.get('MACD_SIGNAL', []))
        bb_upper = pd.Series(indicators.get('BB_UPPER', []))
        bb_lower = pd.Series(indicators.get('BB_LOWER', []))

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

        # Golden Cross / Death Cross
        if len(sma_50) > 1 and len(sma_200) > 1:
            sma50_prev = sma_50.iloc[-2]
            sma200_prev = sma_200.iloc[-2]

            if sma50_prev <= sma200_prev and current_sma50 > current_sma200:
                signals.append({
                    "type": "golden_cross",
                    "signal": "buy",
                    "strength": 0.7,
                    "description": "SMA 50 crossed above SMA 200 (bullish)"
                })
            elif sma50_prev >= sma200_prev and current_sma50 < current_sma200:
                signals.append({
                    "type": "death_cross",
                    "signal": "sell",
                    "strength": 0.7,
                    "description": "SMA 50 crossed below SMA 200 (bearish)"
                })

        # RSI oversold/overbought
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

        # MACD crossover
        if len(macd_line) > 1 and len(macd_signal) > 1:
            macd_prev = macd_line.iloc[-2]
            macd_signal_prev = macd_signal.iloc[-2]

            if macd_prev <= macd_signal_prev and current_macd > current_macd_signal:
                signals.append({
                    "type": "macd_bullish",
                    "signal": "buy",
                    "strength": 0.65,
                    "description": "MACD crossed above signal line (bullish)"
                })
            elif macd_prev >= macd_signal_prev and current_macd < current_macd_signal:
                signals.append({
                    "type": "macd_bearish",
                    "signal": "sell",
                    "strength": 0.65,
                    "description": "MACD crossed below signal line (bearish)"
                })

        # Bollinger Bands
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

        # SMA slope
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

    def _find_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Tuple[List[float], List[float]]:
        """Find support and resistance levels using local minima/maxima."""
        if 'high' not in df.columns or 'low' not in df.columns:
            return [], []

        highs = df['high'].values
        lows = df['low'].values

        support_levels = []
        resistance_levels = []

        for i in range(window, len(lows) - window):
            if all(lows[i] <= lows[i - j] for j in range(1, window + 1)) and \
               all(lows[i] <= lows[i + j] for j in range(1, window + 1)):
                support_levels.append(round(float(lows[i]), 2))

        for i in range(window, len(highs) - window):
            if all(highs[i] >= highs[i - j] for j in range(1, window + 1)) and \
               all(highs[i] >= highs[i + j] for j in range(1, window + 1)):
                resistance_levels.append(round(float(highs[i]), 2))

        support_levels = sorted(set([round(s, 2) for s in support_levels]))
        resistance_levels = sorted(set([round(r, 2) for r in resistance_levels]))

        return support_levels[-5:], resistance_levels[-5:]

    def _determine_trend(self, df: pd.DataFrame) -> Tuple[str, float]:
        """Determine the current trend and its strength."""
        close = df['close']

        if len(close) < 200:
            return "neutral", 0.5

        sma_20 = close.rolling(20).mean().iloc[-1]
        sma_50 = close.rolling(50).mean().iloc[-1]
        sma_200 = close.rolling(200).mean().iloc[-1]
        current_price = close.iloc[-1]

        sma20_slope = (close.rolling(20).mean().iloc[-1] - close.rolling(20).mean().iloc[-5]) / close.rolling(20).mean().iloc[-5]
        sma50_slope = (close.rolling(50).mean().iloc[-1] - close.rolling(50).mean().iloc[-10]) / close.rolling(50).mean().iloc[-10]

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

    def _calculate_momentum(self, df: pd.DataFrame) -> Tuple[str, Optional[float]]:
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

    def _generate_summary(self, trend: str, momentum: str, signals: List[Dict[str, Any]], support_levels: List[float], resistance_levels: List[float]) -> str:
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

    def _calculate_confidence(self, df: pd.DataFrame, signals: List[Dict[str, Any]], trend_strength: float) -> float:
        """Calculate confidence in the technical analysis."""
        base_confidence = trend_strength * 0.4

        if signals:
            buy_strength = sum(s['strength'] for s in signals if s['signal'] == 'buy')
            sell_strength = sum(s['strength'] for s in signals if s['signal'] == 'sell')

            max_strength = max(buy_strength, sell_strength)
            total_strength = buy_strength + sell_strength

            if total_strength > 0:
                alignment = max_strength / total_strength
                base_confidence += alignment * 0.3

        data_quality = min(1.0, len(df) / 252) * 0.3
        base_confidence += data_quality

        return min(1.0, base_confidence)


class NewsAnalystNode(BaseNode):
    """News analysis agent that processes news articles for sentiment and catalysts."""

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
        if not news_articles:
            return NewsAnalysis(ticker=ticker)

        sentiments = []
        catalysts = []
        risk_events = []

        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_count = 0

        for article in news_articles:
            title = article.get("title", "")
            description = article.get("description", "")
            text = f"{title} {description}".lower()

            if not text.strip():
                continue

            sentiment = self._simple_sentiment_analysis(text)
            sentiments.append(sentiment)

            published_str = article.get("published_at", "")
            if published_str:
                try:
                    pub_date = datetime.strptime(published_str.split('T')[0], '%Y-%m-%d')
                    if pub_date >= recent_cutoff:
                        recent_count += 1
                except:
                    pass

            catalyst = self._identify_catalyst(text, article)
            if catalyst:
                catalysts.append(catalyst)

            if self._is_risk_event(text):
                risk_events.append({
                    "type": "negative_news",
                    "title": title[:100],
                    "sentiment": sentiment,
                })

        overall_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

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
            catalysts=catalysts[:10],
            key_events=self._summarize_events(catalysts)[:5],
            risk_events=risk_events[:5],
            summary=self._generate_news_summary(overall_sentiment, catalysts, risk_events),
            confidence=min(1.0, len(news_articles) / 20) if news_articles else 0.3,
        )

        return analysis

    def _simple_sentiment_analysis(self, text: str) -> float:
        """Simple rule-based sentiment analysis."""
        positive_words = [
            'gain', 'gains', 'positive', 'up', 'rise', 'rising', 'rose', 'bullish', 'growth', 'profit',
            'profits', 'earnings', 'beat', 'exceeds', 'strong', 'strength', 'success', 'successful',
            'launch', 'announces', 'partnership', 'deal', 'agreement', 'upgrade', 'buy', 'recommend',
            'target', 'opportunity', 'innovation', 'breakthrough', 'patent', 'approval'
        ]

        negative_words = [
            'loss', 'losses', 'negative', 'down', 'fall', 'falling', 'fell', 'bearish', 'decline',
            'drop', 'plunge', 'crash', 'miss', 'misses', 'weak', 'weakness', 'failure', 'failed',
            'recall', 'warning', 'concern', 'investigation', 'scandal', 'downgrade', 'sell', 'cut',
            'reduce', 'layoff', 'lawsuit', 'regulation', 'penalty', 'fine', 'ban'
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

    def _is_risk_event(self, text: str) -> bool:
        """Check if text describes a risk event."""
        risk_indicators = [
            'investigation', 'lawsuit', 'recall', 'scandal', 'fraud', 'regulatory', 'penalty',
            'fine', 'ban', 'restructuring', 'layoff', 'downgrade', 'debt', 'default', 'bankruptcy'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in risk_indicators)

    def _summarize_events(self, catalysts: List[Dict[str, Any]]) -> List[str]:
        """Create brief summaries of key events."""
        summaries = []
        for cat in catalysts[:5]:
            summaries.append(f"{cat['type'].upper()}: {cat['title']}")
        return summaries

    def _generate_news_summary(self, sentiment: float, catalysts: List[Dict[str, Any]], risk_events: List[Dict[str, Any]]) -> str:
        """Generate narrative summary of news analysis."""
        parts = []

        if sentiment > 0.3:
            parts.append("News sentiment is predominantly positive.")
        elif sentiment < -0.3:
            parts.append("News sentiment is predominantly negative.")
        else:
            parts.append("News sentiment is neutral to mixed.")

        if catalysts:
            catalyst_types = [c['type'] for c in catalysts[:5]]
            parts.append(f"Identified {len(catalysts)} catalysts including {', '.join(set(catalyst_types[:3]))}.")

        if risk_events:
            parts.append(f"Detected {len(risk_events)} potential risk events.")

        return " ".join(parts)


class FundamentalsAnalystNode(BaseNode):
    """Fundamental analysis agent that evaluates financial health and valuation."""

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

        pe_ratio = get_metric(['pe_ratio', 'priceEarningsRatio', 'PE Ratio'], None)
        pb_ratio = get_metric(['pb_ratio', 'priceToBookRatio', 'Price to Book'], None)
        ps_ratio = get_metric(['ps_ratio', 'priceToSalesRatio', 'Price to Sales'], None)
        peg_ratio = get_metric(['peg_ratio', 'pegRatio', 'PEG Ratio'], None)
        roe = get_metric(['roe', 'returnOnEquity', 'ROE'], None)
        roa = get_metric(['roa', 'returnOnAssets', 'ROA'], None)
        net_margin = get_metric(['net_margin', 'netProfitMargin', 'Net Margin'], None)
        operating_margin = get_metric(['operating_margin', 'operatingProfitMargin', 'Operating Margin'], None)
        revenue_growth = get_metric(['revenue_growth', 'revenueGrowth', 'Revenue Growth'], None)
        eps_growth = get_metric(['eps_growth', 'epsGrowth', 'EPS Growth'], None)
        debt_to_equity = get_metric(['debt_to_equity', 'debtToEquity', 'Debt/Equity'], None)
        current_ratio = get_metric(['current_ratio', 'currentRatio', 'Current Ratio'], None)

        fcf = None
        if 'cashflow' in financials:
            cashflow_df = financials['cashflow']
            if isinstance(cashflow_df, dict):
                fcf = cashflow_df.get('freeCashFlow', cashflow_df.get('Free Cash Flow', None))
                if isinstance(fcf, list) and len(fcf) > 0:
                    fcf = fcf[0]

        valuation, fair_value = self._assess_valuation(pe_ratio, pb_ratio, metrics)
        strengths, weaknesses = self._assess_strengths_weaknesses(roe, revenue_growth, debt_to_equity, current_ratio, net_margin)
        summary = self._generate_fundamental_summary(valuation, pe_ratio, roe, revenue_growth, debt_to_equity, strengths, weaknesses)
        confidence = self._calculate_confidence(has_pe=pe_ratio is not None, has_financials=bool(financials), metrics_count=len([m for m in [pe_ratio, pb_ratio, roe, revenue_growth] if m is not None]))

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

    def _assess_valuation(self, pe_ratio: Optional[float], pb_ratio: Optional[float], metrics: Dict[str, Any]) -> Tuple[str, Optional[float]]:
        """Assess whether stock is undervalued, fair, or overvalued."""
        if pe_ratio is None:
            return "fair", None

        if pe_ratio < 10:
            return "undervalued", None
        elif pe_ratio > 30:
            return "overvalued", None
        else:
            return "fair", None

    def _assess_strengths_weaknesses(self, roe: Optional[float], revenue_growth: Optional[float], debt_to_equity: Optional[float], current_ratio: Optional[float], net_margin: Optional[float]) -> Tuple[List[str], List[str]]:
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

    def _generate_fundamental_summary(self, valuation: str, pe_ratio: Optional[float], roe: Optional[float], revenue_growth: Optional[float], debt_to_equity: Optional[float], strengths: List[str], weaknesses: List[str]) -> str:
        """Generate narrative summary."""
        parts = []

        if pe_ratio:
            parts.append(f"P/E ratio of {pe_ratio:.1f} indicates stock is {valuation}.")

        if roe:
            parts.append(f"ROE of {roe:.1f}% demonstrates {'strong' if roe > 15 else 'moderate' if roe > 10 else 'weak'} profitability.")

        if revenue_growth:
            parts.append(f"Revenue growth of {revenue_growth:.1f}%.")

        if debt_to_equity:
            parts.append(f"Debt-to-equity of {debt_to_equity:.2f}.")

        if strengths:
            parts.append(f"Key strengths: {'; '.join(strengths[:2])}.")
        if weaknesses:
            parts.append(f"Key concerns: {'; '.join(weaknesses[:2])}.")

        return " ".join(parts)

    def _calculate_confidence(self, has_pe: bool, has_financials: bool, metrics_count: int) -> float:
        """Calculate confidence in fundamental analysis."""
        confidence = 0.3

        if has_pe:
            confidence += 0.25
        if has_financials:
            confidence += 0.25

        metrics_score = min(metrics_count / 8.0, 1.0) * 0.2
        confidence += metrics_score

        return min(1.0, confidence)


class GrowthAnalystNode(BaseNode):
    """Growth analysis agent that evaluates future growth potential."""

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

        revenue_growth = get_metric(['revenue_growth', 'revenueGrowth', 'Revenue Growth'], None)
        eps_growth = get_metric(['eps_growth', 'epsGrowth', 'EPS Growth'], None)

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

        revenue_cagr = self._estimate_cagr(ticker_data, 'revenue' if 'revenue' in str(financials) else None)
        next_quarter_est = get_metric(['next_quarter_est', 'estimatedEarningsAvg', 'Earnings Estimate'], None)
        next_year_est = get_metric(['next_year_est', 'estimatedRevenueAvg', 'Revenue Estimate'], None)
        long_term_growth = get_metric(['long_term_growth', 'longTermGrowth', 'LT Growth'], None)

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

        growth_score = self._calculate_growth_score(revenue_growth, eps_growth, revenue_cagr, rd_to_revenue, long_term_growth)
        revenue_trend = self._assess_growth_trend(revenue_growth, revenue_cagr)
        summary = self._generate_growth_summary(growth_score, revenue_growth, eps_growth, revenue_trend, rd_to_revenue)
        confidence = self._calculate_growth_confidence(has_revenue_growth=revenue_growth is not None, has_eps_growth=eps_growth is not None, has_estimates=next_year_est is not None)

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
        return None

    def _calculate_growth_score(self, revenue_growth: Optional[float], eps_growth: Optional[float], cagr: Optional[float], rd_to_revenue: Optional[float], long_term_growth: Optional[float]) -> float:
        """Calculate composite growth score (0-100)."""
        score = 50.0

        if revenue_growth:
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

        if rd_to_revenue:
            if rd_to_revenue > 15:
                score += 20
            elif rd_to_revenue > 10:
                score += 15
            elif rd_to_revenue > 5:
                score += 10

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

        if historical is None:
            if current_growth > 15:
                return "accelerating"
            elif current_growth < 0:
                return "declining"
            else:
                return "stable"

        if current_growth > historical * 1.1:
            return "accelerating"
        elif current_growth < historical * 0.9:
            return "decelerating"
        else:
            return "stable"

    def _generate_growth_summary(self, score: float, revenue_growth: Optional[float], eps_growth: Optional[float], trend: str, rd_to_revenue: Optional[float]) -> str:
        """Generate narrative summary."""
        parts = []

        if score >= 70:
            parts.append("Strong growth profile with excellent expansion potential.")
        elif score >= 50:
            parts.append("Moderate growth prospects with steady expansion.")
        elif score >= 30:
            parts.append("Limited growth potential with some constraints.")
        else:
            parts.append("Weak growth outlook with significant headwinds.")

        if revenue_growth:
            parts.append(f"Revenue growth at {revenue_growth:.1f}% shows {'strong' if revenue_growth > 10 else 'moderate' if revenue_growth > 0 else 'declining'} performance.")

        if eps_growth:
            parts.append(f"EPS growth of {eps_growth:.1f}% indicates {'robust' if eps_growth > 15 else 'positive' if eps_growth > 0 else 'weak'} earnings momentum.")

        if rd_to_revenue:
            parts.append(f"R&D investment at {rd_to_revenue:.1f}% of revenue supports future innovation.")

        parts.append(f"Growth trend is {trend}.")

        return " ".join(parts)

    def _calculate_growth_confidence(self, has_revenue_growth: bool, has_eps_growth: bool, has_estimates: bool) -> float:
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
    """Risk analysis agent that evaluates various risk factors."""

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
        returns = self._calculate_returns(ticker_data.historical_data)
        volatility = self._calculate_volatility(returns) if len(returns) > 0 else 0.0
        var_95, cvar_95 = self._calculate_var_cvar(returns, 0.05)
        max_drawdown, current_drawdown = self._calculate_drawdowns(ticker_data.historical_data)
        beta = self._estimate_beta(returns)

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
        avg_volume = self._estimate_avg_volume(ticker_data.historical_data)

        risk_score = self._calculate_risk_score(volatility, max_drawdown, debt_to_equity, current_ratio, beta)

        if risk_score < 30:
            risk_level = "low"
        elif risk_score < 60:
            risk_level = "medium"
        else:
            risk_level = "high"

        summary = self._generate_risk_summary(volatility, max_drawdown, beta, debt_to_equity, risk_level)
        confidence = self._calculate_risk_confidence(returns_available=len(returns) > 0, has_financials=bool(financials), volatility_calculated=volatility > 0)

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

        daily_vol = np.std(returns, ddof=1)

        if annualize:
            return float(daily_vol * np.sqrt(252))
        return float(daily_vol)

    def _calculate_var_cvar(self, returns: List[float], alpha: float = 0.05) -> Tuple[Optional[float], Optional[float]]:
        """Calculate Value at Risk and Conditional VaR."""
        if len(returns) < 30:
            return None, None

        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * alpha)
        var_95 = -sorted_returns[var_index]

        cvar_returns = sorted_returns[:var_index]
        if cvar_returns:
            cvar_95 = -sum(cvar_returns) / len(cvar_returns)
        else:
            cvar_95 = var_95

        return float(var_95), float(cvar_95)

    def _calculate_drawdowns(self, historical_data: Dict[str, List[Any]]) -> Tuple[Optional[float], Optional[float]]:
        """Calculate maximum and current drawdowns."""
        if 'close' not in historical_data:
            return None, None

        closes = [float(c) for c in historical_data['close'] if c is not None]
        if len(closes) < 2:
            return None, None

        running_max = np.maximum.accumulate(closes)
        drawdown = (closes - running_max) / running_max

        max_drawdown = float(np.min(drawdown)) * 100
        current_drawdown = float(drawdown[-1]) * 100 if drawdown[-1] < 0 else 0.0

        return max_drawdown, current_drawdown

    def _estimate_beta(self, returns: List[float]) -> Optional[float]:
        """Estimate beta relative to market."""
        if len(returns) < 60:
            return 1.0

        vol = self._calculate_volatility(returns, annualize=False)
        market_daily_vol = 0.012
        estimated_beta = vol / market_daily_vol if market_daily_vol > 0 else 1.0

        return max(0.0, min(3.0, estimated_beta))

    def _estimate_avg_volume(self, historical_data: Dict[str, List[Any]]) -> Optional[float]:
        """Estimate average daily volume."""
        if 'volume' not in historical_data:
            return None

        volumes = [float(v) for v in historical_data['volume'] if v is not None]
        if not volumes:
            return None

        return float(sum(volumes) / len(volumes))

    def _calculate_risk_score(self, volatility: float, max_drawdown: Optional[float], debt_to_equity: Optional[float], current_ratio: Optional[float], beta: Optional[float]) -> float:
        """Calculate composite risk score (0-100, higher = riskier)."""
        score = 0.0

        if volatility < 0.15:
            score += 5
        elif volatility < 0.25:
            score += 15
        else:
            score += 25

        if max_drawdown:
            if max_drawdown < 20:
                score += 5
            elif max_drawdown < 40:
                score += 15
            else:
                score += 25

        if debt_to_equity:
            if debt_to_equity < 0.5:
                score += 5
            elif debt_to_equity < 1.5:
                score += 15
            else:
                score += 25
        else:
            score += 10

        if beta:
            if beta < 0.8:
                score += 5
            elif beta < 1.2:
                score += 15
            else:
                score += 25
        else:
            score += 10

        return min(100.0, score)

    def _generate_risk_summary(self, volatility: float, max_drawdown: Optional[float], beta: Optional[float], debt_to_equity: Optional[float], risk_level: str) -> str:
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

    def _calculate_risk_confidence(self, returns_available: bool, has_financials: bool, volatility_calculated: bool) -> float:
        """Calculate confidence in risk analysis."""
        confidence = 0.3

        if returns_available:
            confidence += 0.4
        if volatility_calculated:
            confidence += 0.2
        if has_financials:
            confidence += 0.1

        return min(1.0, confidence)


class MacroAnalystNode(BaseNode):
    """Node for macroeconomic and sector analysis."""

    def __init__(self):
        super().__init__("macro_analyst_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Perform macro analysis on all tickers."""
        self.log("Performing macro analysis")

        for ticker, ticker_data in state.ticker_data.items():
            try:
                self.log(f"Analyzing macro factors for {ticker}")
                analysis = self._analyze_macro(ticker, ticker_data)

                if not hasattr(state, 'macro_analyses'):
                    state.macro_analyses = {}

                state.macro_analyses[ticker] = analysis
                self.log(f"Macro analysis for {ticker}: score {analysis.macro_score:.1f}/100")
            except Exception as e:
                self.log(f"Error in macro analysis for {ticker}: {e}", "ERROR")
                state.add_error(self.node_id, str(e), ticker)

        self.log(f"Completed macro analysis: {len(state.macro_analyses if hasattr(state, 'macro_analyses') else {}) } tickers")
        state.completed_nodes.append(self.node_id)
        return state

    def _analyze_macro(self, ticker: str, ticker_data: TickerData) -> MacroAnalysis:
        """Perform macro analysis for a single ticker."""
        sector = self._detect_sector(ticker_data)
        sector_sensitivity = self._get_sector_sensitivity(sector)
        interest_rate_sensitivity = self._estimate_interest_rate_sensitivity(ticker_data)
        macro_score = self._calculate_macro_score(sector, sector_sensitivity, interest_rate_sensitivity)

        return MacroAnalysis(
            ticker=ticker,
            sector=sector,
            sector_rotation_indicator="Neutral",
            sector_relative_strength=0.5,
            interest_rate_sensitivity=interest_rate_sensitivity,
            inflation_sensitivity=0.3,
            economic_cycle_position="Mid-cycle",
            regulatory_factors=[],
            macro_score=macro_score,
            summary=self._generate_macro_summary(sector, macro_score),
            confidence=0.70,
            analyst_type=AnalystType.MACRO,
        )

    def _detect_sector(self, ticker_data: TickerData) -> str:
        """Detect sector from company industry."""
        if hasattr(ticker_data, 'company_info') and ticker_data.company_info:
            if isinstance(ticker_data.company_info, dict):
                sector = ticker_data.company_info.get('sector', 'Technology')
                if sector:
                    return sector

        return "Technology"

    def _get_sector_sensitivity(self, sector: str) -> float:
        """Get macro sensitivity for sector."""
        sensitivity = {
            "Financials": 0.8,
            "Industrials": 0.7,
            "Consumer": 0.5,
            "Technology": 0.4,
            "Healthcare": 0.3,
            "Utilities": 0.2,
            "Energy": 0.9,
        }
        return sensitivity.get(sector, 0.5)

    def _estimate_interest_rate_sensitivity(self, ticker_data: TickerData) -> float:
        """Estimate how sensitive the stock is to interest rates."""
        return 0.5

    def _calculate_macro_score(self, sector: str, sector_sensitivity: float, rate_sensitivity: float) -> float:
        """Calculate composite macro favorability score (0-100)."""
        base_score = 50.0

        if sector in ["Technology", "Healthcare"]:
            base_score += 10
        elif sector in ["Energy", "Utilities"]:
            base_score -= 5

        return min(100.0, max(0.0, base_score))

    def _generate_macro_summary(self, sector: str, macro_score: float) -> str:
        """Generate narrative summary of macro analysis."""
        if macro_score > 60:
            condition = "favorable"
        elif macro_score > 40:
            condition = "neutral"
        else:
            condition = "challenging"

        return f"{sector} sector outlook is {condition}. Macro score: {macro_score:.0f}/100."
