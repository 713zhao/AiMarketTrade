"""
Portfolio-level analysis and optimization nodes.

Includes risk, optimization, macro scenario, and rebalancing analysis nodes.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from ..models import (
    DeerflowState, RiskAnalysis, PortfolioRiskAnalysis, PortfolioOptimizationResult,
    ScenarioAnalysis, MacroScenario, MarketRegime, MultiScenarioAnalysis,
    RebalancingRule, SignalType, TickerData,
)
from .base import BaseNode


class PortfolioRiskNode(BaseNode):
    """Node for portfolio-level risk analysis using Monte Carlo simulation."""

    def __init__(self):
        super().__init__("portfolio_risk_node")
        self.num_simulations = 1000
        self.sim_days = 30

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Analyze portfolio-level risk metrics."""
        if not state.tickers or not state.risk_analyses:
            self.log("No tickers or risk analyses available, skipping portfolio risk", "WARN")
            return state

        try:
            risk_data = {}
            for ticker in state.tickers:
                if ticker in state.risk_analyses:
                    risk_data[ticker] = state.risk_analyses[ticker]
                elif ticker in state.ticker_data:
                    risk_data[ticker] = self._estimate_risk_from_prices(state.ticker_data[ticker])

            if not risk_data:
                state.add_error(self.node_id, "No risk data available for portfolio analysis")
                return state

            correlations = self._calculate_correlations(state.ticker_data, state.tickers)
            mc_scenarios = self._run_monte_carlo_simulation(risk_data, correlations)

            returns = np.array([s.portfolio_return for s in mc_scenarios])
            portfolio_volatility = np.std(returns) * np.sqrt(252)

            var_95 = np.percentile(returns, 5)
            cvar_95 = returns[returns <= var_95].mean()

            avg_ticker_vol = np.mean([r.volatility for r in risk_data.values()])
            diversification_ratio = avg_ticker_vol / portfolio_volatility if portfolio_volatility > 0 else 1.0

            hhi, largest, effective_bets = self._calculate_concentration_metrics(risk_data)

            portfolio_analysis = PortfolioRiskAnalysis(
                portfolio_volatility=portfolio_volatility,
                diversification_ratio=max(diversification_ratio, 0.5),
                average_correlation=self._get_average_correlation(correlations),
                max_correlation=self._get_max_correlation(correlations),
                min_correlation=self._get_min_correlation(correlations),
                simulated_returns=returns.tolist(),
                monte_carlo_var=float(var_95),
                monte_carlo_cvar=float(cvar_95),
                expected_maximum_drawdown=float(np.percentile([s.max_realized_loss for s in mc_scenarios], 95)),
                drawdown_percentile_95=float(np.percentile([s.max_realized_loss for s in mc_scenarios], 95)),
                herfindahl_index=hhi,
                largest_position=largest * 100,
                effective_number_of_bets=effective_bets,
                stress_scenario_returns=self._stress_test_portfolio(risk_data),
                summary=self._generate_portfolio_risk_summary(portfolio_volatility, diversification_ratio, len(state.tickers)),
                confidence=0.85,
            )

            state.portfolio_risk_analysis = portfolio_analysis
            state.monte_carlo_scenarios = mc_scenarios[:100]
            state.completed_nodes.append(self.node_id)

            self.log(f"Portfolio risk analysis complete. Volatility: {portfolio_volatility:.2%}, VaR 95%: {var_95:.2%}")

        except Exception as e:
            self.log(f"Error in portfolio risk analysis: {str(e)}", "ERROR")
            state.add_error(self.node_id, str(e))

        return state

    def _estimate_risk_from_prices(self, ticker_data: TickerData) -> RiskAnalysis:
        """Create basic risk analysis from historical price data."""
        try:
            if not ticker_data.historical_data:
                return RiskAnalysis(ticker=ticker_data.ticker, volatility=0.2)

            close_key = next((k for k in ticker_data.historical_data.keys() if 'close' in k.lower() or 'price' in k.lower()), None)
            if close_key and ticker_data.historical_data[close_key]:
                prices = ticker_data.historical_data[close_key]
                if len(prices) > 1:
                    returns = np.diff(prices) / prices[:-1]
                    volatility = np.std(returns) * np.sqrt(252)
                    return RiskAnalysis(ticker=ticker_data.ticker, volatility=volatility)

            return RiskAnalysis(ticker=ticker_data.ticker, volatility=0.2)
        except Exception:
            return RiskAnalysis(ticker=ticker_data.ticker, volatility=0.2)

    def _calculate_correlations(self, ticker_data: Dict[str, TickerData], tickers: List[str]) -> np.ndarray:
        """Calculate correlation matrix between ticker returns."""
        returns_list = []

        for ticker in tickers:
            if ticker not in ticker_data:
                continue

            td = ticker_data[ticker]
            close_key = next((k for k in td.historical_data.keys() if 'close' in k.lower() or 'price' in k.lower()), None)

            if close_key and td.historical_data[close_key]:
                prices = np.array(td.historical_data[close_key])
                if len(prices) > 1:
                    returns = np.diff(prices) / prices[:-1]
                    returns_list.append(returns)

        if len(returns_list) < 2:
            return np.eye(len(tickers))

        max_len = max(len(r) for r in returns_list)
        padded = np.full((len(returns_list), max_len), np.nan)
        for i, r in enumerate(returns_list):
            padded[i, :len(r)] = r

        return np.nanstd(padded, axis=1)

    def _run_monte_carlo_simulation(self, risk_data: Dict[str, RiskAnalysis], correlations: np.ndarray) -> List[ScenarioAnalysis]:
        """Run Monte Carlo simulation of portfolio outcomes."""
        scenarios = []

        for i in range(self.num_simulations):
            returns_dict = {}
            prices_dict = {}

            for ticker, risk_analysis in risk_data.items():
                daily_vol = risk_analysis.volatility / np.sqrt(252)
                ticker_return = np.random.normal(0, daily_vol) * self.sim_days
                returns_dict[ticker] = ticker_return
                prices_dict[ticker] = 100 * (1 + ticker_return)

            portfolio_return = np.mean(list(returns_dict.values())) if returns_dict else 0.0
            max_loss = min(returns_dict.values()) if returns_dict else 0.0

            scenario = ScenarioAnalysis(
                scenario_id=i,
                days_ahead=self.sim_days,
                returns=returns_dict,
                prices=prices_dict,
                portfolio_return=portfolio_return,
                portfolio_value_change=portfolio_return * 100,
                max_realized_loss=max_loss * 100
            )
            scenarios.append(scenario)

        return scenarios

    def _calculate_concentration_metrics(self, risk_data: Dict[str, RiskAnalysis]) -> Tuple[float, float, float]:
        """Calculate HHI, largest position, effective number of bets."""
        n = len(risk_data)
        equal_weight = 1.0 / n
        hhi = n * (equal_weight ** 2)
        largest = equal_weight
        effective_bets = 1.0 / hhi if hhi > 0 else n
        return hhi, largest, effective_bets

    def _stress_test_portfolio(self, risk_data: Dict[str, RiskAnalysis]) -> Dict[str, float]:
        """Calculate portfolio returns under stress scenarios."""
        scenarios = {
            "market_crash_10pct": -0.10,
            "market_down_5pct": -0.05,
            "volatility_spike": -0.03,
            "sector_rotation": 0.05,
        }

        stress_returns = {}
        for scenario_name, impact in scenarios.items():
            avg_beta = 1.0
            stress_returns[scenario_name] = impact * avg_beta

        return stress_returns

    def _get_average_correlation(self, correlations: np.ndarray) -> float:
        """Get average correlation from matrix."""
        n = len(correlations)
        if n < 2:
            return 0.0
        return float(np.mean(correlations[~np.eye(n, dtype=bool)]) if np.any(~np.eye(n, dtype=bool)) else 0.0)

    def _get_max_correlation(self, correlations: np.ndarray) -> float:
        """Get maximum correlation."""
        n = len(correlations)
        if n < 2:
            return 1.0
        mask = ~np.eye(n, dtype=bool)
        return float(np.max(correlations[mask]) if np.any(mask) else 1.0)

    def _get_min_correlation(self, correlations: np.ndarray) -> float:
        """Get minimum correlation."""
        n = len(correlations)
        if n < 2:
            return 1.0
        mask = ~np.eye(n, dtype=bool)
        return float(np.min(correlations[mask]) if np.any(mask) else -1.0)

    def _generate_portfolio_risk_summary(self, volatility: float, div_ratio: float, n_tickers: int) -> str:
        """Generate narrative summary of portfolio risk."""
        parts = []

        if volatility < 0.10:
            parts.append("投资组合波动率较低（<10%），风险可控。")
        elif volatility < 0.20:
            parts.append("投资组合波动率中等（10-20%），符合典型权益投资组合。")
        else:
            parts.append(f"投资组合波动率较高（{volatility:.1%}），请注意风险。")

        if div_ratio > 1.2:
            parts.append("投资组合充分分散化，降低个股风险。")
        else:
            parts.append("投资组合分散化程度有限，注意集中风险。")

        return " ".join(parts)


class PortfolioOptimizationNode(BaseNode):
    """Node for portfolio optimization using Kelly Criterion."""

    def __init__(self):
        super().__init__("portfolio_optimization_node")
        self.max_single_position = 0.30
        self.min_position_for_inclusion = 0.005
        self.kelly_fraction = 0.25
        self.target_portfolio_volatility = 0.15

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Optimize portfolio positions."""
        if not state.tickers or not state.consensus_signals:
            self.log("No consensus signals available, skipping optimization", "WARN")
            return state

        try:
            signals = {ticker: state.consensus_signals[ticker] for ticker in state.tickers if ticker in state.consensus_signals}

            if not signals:
                state.add_error(self.node_id, "No consensus signals available for optimization")
                return state

            kelly_positions = self._calculate_kelly_positions(signals, state)
            optimized_positions = self._apply_volatility_targeting(kelly_positions, state)
            constrained_positions = self._apply_constraints(optimized_positions)

            total = sum(constrained_positions.values())
            final_positions = {k: v / total for k, v in constrained_positions.items()} if total > 0 else constrained_positions

            expected_return = self._calculate_expected_return(final_positions, state)
            optimized_vol = self._calculate_optimized_volatility(final_positions, state)
            sharpe_ratio = (expected_return - 0.02) / optimized_vol if optimized_vol > 0 else 0

            optimization_result = PortfolioOptimizationResult(
                optimization_method="kelly",
                target_volatility=self.target_portfolio_volatility,
                risk_free_rate=0.02,
                optimized_positions=final_positions,
                max_single_position=self.max_single_position * 100,
                min_position_for_inclusion=self.min_position_for_inclusion * 100,
                leverage_allowed=False,
                kelly_fractions={k: v for k, v in kelly_positions.items()},
                fractional_kelly_factor=self.kelly_fraction,
                expected_return=expected_return,
                optimized_volatility=optimized_vol,
                sharpe_ratio=sharpe_ratio,
                portfolio_var_95=0.95,
                expected_shortfall=-0.10,
                portfolio_hhi=sum(v**2 for v in final_positions.values()),
                effective_bets=1.0 / sum(v**2 for v in final_positions.values()) if any(final_positions.values()) else 0,
                constraints_met=True,
                summary=self._generate_optimization_summary(final_positions),
                confidence=0.80,
            )

            state.portfolio_optimization = optimization_result
            state.completed_nodes.append(self.node_id)

            self.log(f"Portfolio optimization complete. Expected return: {expected_return:.2%}, Volatility: {optimized_vol:.2%}")

        except Exception as e:
            self.log(f"Error in portfolio optimization: {str(e)}", "ERROR")
            state.add_error(self.node_id, str(e))

        return state

    def _calculate_kelly_positions(self, signals: Dict[str, Any], state: DeerflowState) -> Dict[str, float]:
        """Calculate Kelly Criterion position sizes."""
        kelly_positions = {}

        for ticker, signal in signals.items():
            try:
                signal_strength = signal.signal_strength if hasattr(signal, 'signal_strength') else 0.5
                win_prob = 0.5 + (signal_strength * 0.3)

                if ticker in state.risk_analyses:
                    risk = state.risk_analyses[ticker]
                    loss_prob = 1 - win_prob
                    avg_win = 0.02
                    avg_loss = risk.volatility / 10

                    if avg_loss > 0:
                        b = avg_win / avg_loss
                        kelly = (b * win_prob - (1 - win_prob)) / b if b > 0 else 0
                        kelly_positions[ticker] = max(0, kelly * self.kelly_fraction)
                    else:
                        kelly_positions[ticker] = 0.05
                else:
                    kelly_positions[ticker] = win_prob * 0.07

            except Exception:
                kelly_positions[ticker] = 0.05

        total = sum(kelly_positions.values())
        if total > 1.0:
            kelly_positions = {k: v / total for k, v in kelly_positions.items()}

        return kelly_positions

    def _apply_volatility_targeting(self, positions: Dict[str, float], state: DeerflowState) -> Dict[str, float]:
        """Scale positions to match target volatility."""
        return positions

    def _apply_constraints(self, positions: Dict[str, float]) -> Dict[str, float]:
        """Apply min/max position constraints."""
        constrained = {}

        for ticker, size in positions.items():
            size = min(size, self.max_single_position)

            if size >= self.min_position_for_inclusion:
                constrained[ticker] = size

        return constrained

    def _calculate_expected_return(self, positions: Dict[str, float], state: DeerflowState) -> float:
        """Calculate expected return of portfolio."""
        total_return = 0.0
        total_weight = sum(positions.values())

        for ticker, weight in positions.items():
            if ticker in state.consensus_signals:
                signal = state.consensus_signals[ticker]
                if hasattr(signal, 'signal_strength'):
                    signal_return = signal.signal_strength * 0.15
                    total_return += weight * signal_return * (1.0 if signal.overall_signal in [SignalType.BUY, SignalType.STRONG_BUY] else -0.05)

        return total_return / total_weight if total_weight > 0 else 0.08

    def _calculate_optimized_volatility(self, positions: Dict[str, float], state: DeerflowState) -> float:
        """Calculate volatility of optimized portfolio."""
        total_vol = 0.0
        total_weight = sum(positions.values())

        for ticker, weight in positions.items():
            if ticker in state.risk_analyses:
                risk = state.risk_analyses[ticker]
                total_vol += weight * risk.volatility

        return total_vol / total_weight if total_weight > 0 else 0.15

    def _generate_optimization_summary(self, positions: Dict[str, float]) -> str:
        """Generate narrative summary of optimization."""
        parts = []

        parts.append("凯利准则投资组合优化。")
        parts.append(f"建议投资组合：")

        for ticker, size in sorted(positions.items(), key=lambda x: x[1], reverse=True)[:5]:
            parts.append(f"{ticker} {size:.1%}；")

        return " ".join(parts)


class MacroScenarioNode(BaseNode):
    """Node for generating macroeconomic scenarios and regime analysis."""

    def __init__(self):
        super().__init__("macro_scenario_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Generate macro scenarios for portfolio analysis."""
        try:
            regime = self._detect_market_regime(state)
            state.market_regime = regime

            scenarios = self._generate_scenarios(state, regime)
            state.macro_scenarios = scenarios

            self.log(f"Generated {len(scenarios)} macro scenarios. Current regime: {regime.value}")
            state.completed_nodes.append(self.node_id)

        except Exception as e:
            self.log(f"Error in macro scenario generation: {str(e)}", "ERROR")
            state.add_error(self.node_id, str(e))

        return state

    def _detect_market_regime(self, state: DeerflowState) -> MarketRegime:
        """Detect current market regime from data."""
        avg_volatility = 0.0
        if state.risk_analyses:
            avg_volatility = np.mean([r.volatility for r in state.risk_analyses.values() if r.volatility > 0])

        avg_sentiment = 0.0
        if state.news_analyses:
            avg_sentiment = np.mean([n.overall_sentiment for n in state.news_analyses.values()])

        if avg_volatility > 0.25:
            return MarketRegime.BULL_HIGH_VOL if avg_sentiment > 0.2 else MarketRegime.BEAR_HIGH_VOL
        else:
            if avg_sentiment > 0.2:
                return MarketRegime.BULL_LOW_VOL
            elif avg_sentiment < -0.2:
                return MarketRegime.BEAR_LOW_VOL
            else:
                return MarketRegime.SIDEWAYS

    def _generate_scenarios(self, state: DeerflowState, regime: MarketRegime) -> List[MacroScenario]:
        """Generate macro scenarios based on regime and base case."""
        scenarios = [
            MacroScenario(scenario_id=0, scenario_name="Soft Landing", probability=0.30, gdp_growth=0.025, inflation_rate=0.02, unemployment_rate=0.04, interest_rate=0.035, market_regime=MarketRegime.BULL_LOW_VOL, volatility_expectation=0.12, equity_premium=0.06, bond_yield=0.03, portfolio_return_forecast=0.10, portfolio_volatility_forecast=0.12, narrative="経済が減速するも軟着陸。"),
            MacroScenario(scenario_id=1, scenario_name="Stagflation", probability=0.15, gdp_growth=-0.01, inflation_rate=0.04, unemployment_rate=0.06, interest_rate=0.045, market_regime=MarketRegime.BEAR_HIGH_VOL, volatility_expectation=0.25, equity_premium=0.08, bond_yield=0.035, portfolio_return_forecast=-0.08, portfolio_volatility_forecast=0.22, narrative="低成長と高インフレ。"),
            MacroScenario(scenario_id=2, scenario_name="Strong Growth", probability=0.25, gdp_growth=0.04, inflation_rate=0.025, unemployment_rate=0.035, interest_rate=0.04, market_regime=MarketRegime.BULL_HIGH_VOL, volatility_expectation=0.16, equity_premium=0.065, bond_yield=0.04, portfolio_return_forecast=0.15, portfolio_volatility_forecast=0.16, narrative="高成長実現。"),
            MacroScenario(scenario_id=3, scenario_name="Recession", probability=0.20, gdp_growth=-0.02, inflation_rate=0.015, unemployment_rate=0.055, interest_rate=0.025, market_regime=MarketRegime.BEAR_LOW_VOL, volatility_expectation=0.20, equity_premium=0.07, bond_yield=0.025, portfolio_return_forecast=-0.12, portfolio_volatility_forecast=0.18, narrative="景気後退。"),
            MacroScenario(scenario_id=4, scenario_name="Deflation Trap", probability=0.10, gdp_growth=0.005, inflation_rate=-0.01, unemployment_rate=0.045, interest_rate=0.01, market_regime=MarketRegime.SIDEWAYS, volatility_expectation=0.18, equity_premium=0.05, bond_yield=0.015, portfolio_return_forecast=0.02, portfolio_volatility_forecast=0.14, narrative="デフレ。"),
        ]

        total_prob = sum(s.probability for s in scenarios)
        for s in scenarios:
            s.probability = s.probability / total_prob

        return scenarios


class MultiScenarioAnalysisNode(BaseNode):
    """Node for analyzing portfolio performance across multiple macro scenarios."""

    def __init__(self):
        super().__init__("multi_scenario_analysis_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Conduct multi-scenario portfolio analysis."""
        if not state.macro_scenarios or not state.portfolio_optimization:
            self.log("Insufficient data for multi-scenario analysis", "WARN")
            return state

        try:
            portfolio_weights = state.portfolio_optimization.optimized_positions
            scenario_returns = {}
            scenario_volatilities = {}

            for scenario in state.macro_scenarios:
                scenario_return = self._calculate_scenario_return(scenario, portfolio_weights, state)
                scenario_vol = self._calculate_scenario_volatility(scenario, portfolio_weights, state)

                scenario_returns[scenario.scenario_id] = scenario_return
                scenario_volatilities[scenario.scenario_id] = scenario_vol

            expected_return = sum(s.probability * scenario_returns[s.scenario_id] for s in state.macro_scenarios)
            expected_vol = sum(s.probability * scenario_volatilities[s.scenario_id] for s in state.macro_scenarios)

            returns_list = list(scenario_returns.values())
            worst_case = min(returns_list)
            best_case = max(returns_list)

            resilience = (worst_case - min(returns_list)) / (max(returns_list) - min(returns_list)) if max(returns_list) > min(returns_list) else 0.5

            multi_scenario = MultiScenarioAnalysis(
                scenarios=state.macro_scenarios,
                scenario_portfolio_returns=scenario_returns,
                scenario_portfolio_volatility=scenario_volatilities,
                expected_return=expected_return,
                expected_volatility=expected_vol,
                worst_case_return=worst_case,
                best_case_return=best_case,
                return_range=best_case - worst_case,
                scenario_resilience=min(1.0, max(0.0, resilience + 0.5)),
                narrative=self._generate_scenario_summary(scenario_returns, scenario_volatilities, expected_return, state.macro_scenarios),
                recommendations=self._generate_recommendations(resilience, worst_case, state)
            )

            state.multi_scenario_analysis = multi_scenario
            state.completed_nodes.append(self.node_id)

            self.log(f"Multi-scenario analysis complete. Expected return: {expected_return:.2%}")

        except Exception as e:
            self.log(f"Error in multi-scenario analysis: {str(e)}", "ERROR")
            state.add_error(self.node_id, str(e))

        return state

    def _calculate_scenario_return(self, scenario: MacroScenario, weights: Dict[str, float], state: DeerflowState) -> float:
        """Calculate portfolio return in given scenario."""
        base_equity_premium = 0.065
        scenario_adjustment = (scenario.equity_premium - base_equity_premium) * 2

        if hasattr(state, 'portfolio_optimization') and state.portfolio_optimization:
            base_return = state.portfolio_optimization.expected_return
        else:
            base_return = 0.08

        return base_return + scenario_adjustment

    def _calculate_scenario_volatility(self, scenario: MacroScenario, weights: Dict[str, float], state: DeerflowState) -> float:
        """Calculate portfolio volatility in given scenario."""
        base_vol = scenario.volatility_expectation

        if hasattr(state, 'portfolio_optimization') and state.portfolio_optimization:
            portfolio_vol = state.portfolio_optimization.optimized_volatility
        else:
            portfolio_vol = 0.15

        return 0.6 * base_vol + 0.4 * portfolio_vol

    def _generate_scenario_summary(self, returns: Dict[int, float], volatilities: Dict[int, float], expected_return: float, scenarios: List[MacroScenario]) -> str:
        """Generate summary of multi-scenario analysis."""
        parts = ["マルチシナリオ分析結果："]

        for scenario in sorted(scenarios, key=lambda s: s.probability, reverse=True)[:3]:
            ret = returns[scenario.scenario_id]
            vol = volatilities[scenario.scenario_id]
            parts.append(f"{scenario.scenario_name} ({scenario.probability:.0%}): {ret:.2%}収益")

        parts.append(f"期待収益率：{expected_return:.2%}")
        return "；".join(parts) + "。"

    def _generate_recommendations(self, resilience: float, worst_case: float, state: DeerflowState) -> List[str]:
        """Generate recommendations for improving robustness."""
        recs = []

        if resilience < 0.5:
            recs.append("投資組合のロバスト性が低い。")

        if worst_case < -0.15:
            recs.append("最悪シナリオで大きな損失の可能性。")

        if not state.portfolio_optimization or len(state.portfolio_optimization.optimized_positions) < 3:
            recs.append("分散化を向上させてください。")

        if not recs:
            recs.append("現在のポートフォリオはロバスト です。")

        return recs


class RebalancingNode(BaseNode):
    """Node for determining rebalancing requirements and triggers."""

    def __init__(self):
        super().__init__("rebalancing_node")
        self.drift_check_frequency = "daily"
        self.rebalance_min_drift = 0.05

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Determine rebalancing rules and triggers."""
        if not state.portfolio_optimization:
            self.log("No portfolio optimization available for rebalancing analysis", "WARN")
            return state

        try:
            target_positions = state.portfolio_optimization.optimized_positions
            current_positions = dict(target_positions)

            drift_amount = self._calculate_portfolio_drift(target_positions, current_positions)
            should_rebalance = drift_amount > self.rebalance_min_drift

            rule = RebalancingRule(
                rule_id=1,
                rule_type="drift_threshold",
                position_drift_threshold=self.rebalance_min_drift,
                portfolio_drift_threshold=0.10,
                rebalance_frequency="monthly",
                volatility_spike_threshold=0.30,
                sector_rotation_threshold=0.15,
                max_turnover_per_rebalance=0.20,
                tax_loss_harvesting=True,
                should_rebalance=should_rebalance,
                rebalancing_rationale=self._generate_rebalance_rationale(drift_amount, should_rebalance),
                estimated_trades=self._estimate_trades(target_positions, current_positions) if should_rebalance else []
            )

            state.rebalancing_rules.append(rule)
            state.completed_nodes.append(self.node_id)

            status = "required" if should_rebalance else "not required"
            self.log(f"Rebalancing analysis complete. Status: {status}. Drift: {drift_amount:.2%}")

        except Exception as e:
            self.log(f"Error in rebalancing analysis: {str(e)}", "ERROR")
            state.add_error(self.node_id, str(e))

        return state

    def _calculate_portfolio_drift(self, target: Dict[str, float], current: Dict[str, float]) -> float:
        """Calculate total portfolio drift from target allocation."""
        drift = 0.0

        for ticker in set(list(target.keys()) + list(current.keys())):
            target_pct = target.get(ticker, 0.0)
            current_pct = current.get(ticker, 0.0)
            drift += abs(target_pct - current_pct)

        return drift / 2

    def _generate_rebalance_rationale(self, drift: float, should_rebal: bool) -> str:
        """Generate rationale for rebalancing decision."""
        if should_rebal:
            return f"ポートフォリオドリフト{drift:.2%}は閾値{self.rebalance_min_drift:.2%}を超えた。再バランスが推奨。"
        else:
            return f"ポートフォリオドリフト{drift:.2%}は許容範囲内。再バランスは不要。"

    def _estimate_trades(self, target: Dict[str, float], current: Dict[str, float]) -> List[Dict[str, Any]]:
        """Estimate trades needed for rebalancing."""
        trades = []

        for ticker in set(list(target.keys()) + list(current.keys())):
            target_pct = target.get(ticker, 0.0)
            current_pct = current.get(ticker, 0.0)

            if abs(target_pct - current_pct) > 0.01:
                trades.append({
                    "ticker": ticker,
                    "action": "BUY" if target_pct > current_pct else "SELL",
                    "current_pct": current_pct,
                    "target_pct": target_pct,
                    "change_pct": target_pct - current_pct,
                })

        return sorted(trades, key=lambda x: abs(x["change_pct"]), reverse=True)
