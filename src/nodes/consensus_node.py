"""
Consensus signal generation and trading decision nodes.

Combines analyst signals into unified consensus and generates final trading decisions.
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import numpy as np

from ..models import (
    DeerflowState, ConsensusSignal, TradingDecision, SignalType, AnalystType,
    TechnicalAnalysis, RiskAnalysis, TickerData,
)
from .base import BaseNode


class ConsensusNode(BaseNode):
    """Consensus aggregation node that combines all analyst signals."""

    def __init__(self):
        super().__init__("consensus_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Generate consensus signals for all tickers with complete analysis."""
        self.log(f"Generating consensus signals")

        weights = {
            AnalystType.TECHNICAL: 0.20,
            AnalystType.FUNDAMENTALS: 0.25,
            AnalystType.NEWS: 0.15,
            AnalystType.GROWTH: 0.15,
            AnalystType.RISK: -0.15,
            AnalystType.MACRO: 0.10,
        }

        for ticker in state.tickers:
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

    async def _generate_consensus(self, ticker: str, analyses: Dict[AnalystType, Any], weights: Dict[AnalystType, float]) -> ConsensusSignal:
        """Generate consensus signal from all analyst outputs."""
        weighted_scores = []
        analyst_signals = {}

        for analyst_type, analysis in analyses.items():
            weight = weights.get(analyst_type, 0.0)
            score = self._convert_to_score(analysis, analyst_type)
            weighted_score = score * abs(weight) * (1 if weight >= 0 else -1)
            weighted_scores.append(weighted_score)
            analyst_signals[analyst_type] = {
                "score": float(score),
                "weight": float(weight),
                "weighted_score": float(weighted_score),
                "confidence": float(analysis.confidence) if hasattr(analysis, 'confidence') else 0.5,
            }

        total_weighted_score = sum(weighted_scores)
        active_weights = sum(abs(weights.get(at, 0)) for at in analyses.keys())
        normalized_score = total_weighted_score / active_weights if active_weights > 0 else 0.0

        overall_signal, signal_strength = self._score_to_signal(normalized_score)

        confidences = [a.confidence for a in analyses.values() if hasattr(a, 'confidence')]
        consensus_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        target_price = None
        if AnalystType.FUNDAMENTALS in analyses:
            fund_analysis = analyses[AnalystType.FUNDAMENTALS]
            if hasattr(fund_analysis, 'fair_value_estimate') and fund_analysis.fair_value_estimate:
                target_price = fund_analysis.fair_value_estimate

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
        """Convert an analysis result to a normalized score (-1 to +1)."""
        if analyst_type == AnalystType.TECHNICAL:
            trend_score = 0.5 if analysis.trend == "bullish" else -0.5 if analysis.trend == "bearish" else 0.0
            momentum_score = 0.3 if analysis.momentum == "oversold" else -0.3 if analysis.momentum == "overbought" else 0.0
            signal_strength = 0.0
            if analysis.signals:
                buy_strength = sum(s['strength'] for s in analysis.signals if s['signal'] == 'buy')
                sell_strength = sum(s['strength'] for s in analysis.signals if s['signal'] == 'sell')
                signal_strength = (buy_strength - sell_strength) / max(1.0, len(analysis.signals))
            return trend_score + momentum_score + signal_strength * 0.5

        elif analyst_type == AnalystType.FUNDAMENTALS:
            score = 0.0
            if analysis.valuation == "undervalued":
                score += 0.6
            elif analysis.valuation == "overvalued":
                score -= 0.6
            if analysis.roe:
                score += 0.2 if analysis.roe > 15 else -0.2 if analysis.roe < 5 else 0
            if analysis.revenue_growth:
                score += 0.2 if analysis.revenue_growth > 10 else -0.2 if analysis.revenue_growth < 0 else 0
            return max(-1.0, min(1.0, score))

        elif analyst_type == AnalystType.NEWS:
            return analysis.overall_sentiment

        elif analyst_type == AnalystType.GROWTH:
            normalized = (analysis.growth_score - 50) / 50.0
            return max(-1.0, min(1.0, normalized))

        elif analyst_type == AnalystType.RISK:
            return -0.3 if analysis.risk_score > 70 else 0.2 if analysis.risk_score < 30 else 0.0

        elif analyst_type == AnalystType.MACRO:
            normalized = (analysis.macro_score - 50) / 50.0
            return max(-1.0, min(1.0, normalized))

        return 0.0

    def _score_to_signal(self, score: float) -> Tuple[SignalType, float]:
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

    def _generate_consensus_rationale(self, analyst_signals: Dict[AnalystType, Dict[str, Any]], overall_signal: SignalType, strength: float) -> str:
        """Generate rationale explaining consensus."""
        parts = []

        if overall_signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            parts.append("Based on综合分析，多数分析师给出买入建议。")
        elif overall_signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            parts.append("基于综合分析，多数分析师建议卖出。")
        else:
            parts.append("综合分析显示信号中性，建议持有。")

        bullish_analysts = sum(1 for s in analyst_signals.values() if s['score'] > 0.2)
        bearish_analysts = sum(1 for s in analyst_signals.values() if s['score'] < -0.2)
        neutral_analysts = len(analyst_signals) - bullish_analysts - bearish_analysts

        parts.append(f"分析师意见：看多{bullish_analysts}位，看空{bearish_analysts}位，中性{neutral_analysts}位。")

        positive_contributors = [at.value for at, s in analyst_signals.items() if s['score'] > 0.3]
        negative_contributors = [at.value for at, s in analyst_signals.items() if s['score'] < -0.3]

        if positive_contributors:
            parts.append(f"看多因素：{', '.join(positive_contributors)}。")
        if negative_contributors:
            parts.append(f"看空因素：{', '.join(negative_contributors)}。")

        return " ".join(parts[:4])


class DecisionNode(BaseNode):
    """Final decision node that synthesizes consensus signal into trading decision."""

    def __init__(self):
        super().__init__("decision_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Generate trading decisions for all analyzed tickers."""
        self.log(f"Generating final trading decisions")

        for ticker in state.tickers:
            if ticker not in state.consensus_signals:
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

        signal_strength = consensus.signal_strength
        overall_signal = consensus.overall_signal

        if overall_signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            action = SignalType.BUY if signal_strength > 0.6 else SignalType.HOLD
        elif overall_signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            action = SignalType.SELL if signal_strength > 0.6 else SignalType.HOLD
        else:
            action = SignalType.HOLD

        if action == SignalType.BUY:
            position_size = self.settings.max_position_size * consensus.consensus_confidence * signal_strength
        elif action == SignalType.SELL:
            position_size = 0.0  # Sell action with position_size=0 indicates no new position
        else:
            position_size = 0.0

        stop_loss = None
        take_profit = None
        risk_reward_ratio = None

        if action == SignalType.BUY and risk_analysis and risk_analysis.volatility > 0:
            if tech_analysis and 'ATR_14' in tech_analysis.indicators:
                atr_value = tech_analysis.indicators['ATR_14'][-1]
                current_price = self._get_current_price(state.ticker_data[ticker])
                if current_price:
                    stop_loss = current_price - 2 * atr_value
                    take_profit = current_price + 4 * atr_value
                    risk_reward_ratio = 4.0 / 2.0

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

    def _generate_rationale(self, consensus: ConsensusSignal, tech_analysis: Optional[TechnicalAnalysis], risk_analysis: Optional[RiskAnalysis], action: SignalType) -> str:
        """Generate comprehensive rationale using all analysts."""
        parts = []

        signal_desc = "买入" if consensus.overall_signal.value in ['buy', 'strong_buy'] else \
                     "卖出" if consensus.overall_signal.value in ['sell', 'strong_sell'] else "持有"
        parts.append(f"综合分析给出{signal_desc}建议，强度{consensus.signal_strength:.0%}，可信度{consensus.consensus_confidence:.0%}。")

        if consensus.analyst_signals:
            parts.append("分析师意见：")
            for at, sig in consensus.analyst_signals.items():
                contribution = "看多" if sig['score'] > 0.2 else "看空" if sig['score'] < -0.2 else "中性"
                parts.append(f"{at.value} {contribution}；")

        if tech_analysis:
            parts.append(f"技术面：{tech_analysis.trend}趋势，{tech_analysis.momentum}动量。")

        if risk_analysis:
            parts.append(f"风险等级：{risk_analysis.risk_level}（波动率{risk_analysis.volatility:.1%}）。")

        if consensus.target_price:
            parts.append(f"目标价${consensus.target_price:.2f}。")

        if action == SignalType.BUY:
            if consensus.signal_strength > 0.7:
                parts.append("强烈推荐买入。")
            else:
                parts.append("建议小仓位买入。")
        elif action == SignalType.SELL:
            parts.append("建议卖出或减仓。")
        else:
            parts.append("暂无明确信号，建议观望。")

        return " ".join(parts[:5])

    def _generate_fallback_rationale(self, tech_analysis: TechnicalAnalysis, action: SignalType, net_signal: float) -> str:
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
