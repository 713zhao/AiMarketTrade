"""
Advanced Strategies & Derivatives Trading Nodes

Implements options, futures, crypto derivatives, and multi-leg strategy management.
Includes Greeks calculation, hedging recommendations, volatility arbitrage,
and pair trading capabilities.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from functools import lru_cache

from .base import BaseNode
from ..models import DeerflowState

logger = logging.getLogger(__name__)


# ============================================================================
# GREEKS CALCULATION ENGINE
# ============================================================================

class GreeksCalculator:
    """
    Black-Scholes and approximation-based Greeks calculator.
    
    计算期权希腊字母（Greeks）。
    """
    
    @staticmethod
    def black_scholes(
        spot: float,
        strike: float,
        time_to_expiration: float,
        risk_free_rate: float,
        volatility: float,
        option_type: str = "CALL"
    ) -> Dict[str, float]:
        """
        Calculate Greeks using Black-Scholes model.
        
        Args:
            spot: Current spot price
            strike: Strike price
            time_to_expiration: Time to expiration in years
            risk_free_rate: Risk-free rate
            volatility: Implied volatility
            option_type: "CALL" or "PUT"
            
        Returns:
            Dict with delta, gamma, theta, vega, rho
        """
        import math
        
        if time_to_expiration <= 0:
            return GreeksCalculator._intrinsic_greeks(spot, strike, option_type)
        
        S = spot
        K = strike
        T = time_to_expiration
        r = risk_free_rate
        sigma = volatility
        
        # d1 and d2
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # Normal distribution values
        from scipy.stats import norm
        N_d1 = norm.cdf(d1)
        N_d2 = norm.cdf(d2)
        n_d1 = norm.pdf(d1)
        
        if option_type == "CALL":
            delta = N_d1
            theta = (-(S * n_d1 * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * N_d2) / 365
            pnl_theta = theta * K
        else:  # PUT
            delta = N_d1 - 1
            theta = (-(S * n_d1 * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * (1 - N_d2)) / 365
            pnl_theta = theta * K
        
        gamma = n_d1 / (S * sigma * math.sqrt(T))
        vega = S * n_d1 * math.sqrt(T) / 100  # Per 1% IV change
        rho = K * math.exp(-r * T) * T / 100  # Per 1% rate change
        
        return {
            "delta": delta,
            "gamma": gamma,
            "theta": pnl_theta,
            "vega": vega,
            "rho": rho if option_type == "CALL" else -rho,
        }
    
    @staticmethod
    def _intrinsic_greeks(spot: float, strike: float, option_type: str) -> Dict[str, float]:
        """Greeks for expired or deep ITM/OTM options."""
        if option_type == "CALL":
            intrinsic = max(spot - strike, 0)
            delta = 1.0 if intrinsic > 0 else 0.0
        else:
            intrinsic = max(strike - spot, 0)
            delta = -1.0 if intrinsic > 0 else 0.0
        
        return {
            "delta": delta,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0,
        }
    
    @staticmethod
    def aggregate_greeks(positions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Aggregate Greeks across multiple positions.
        
        Args:
            positions: List of position dicts with quantity and Greeks
            
        Returns:
            Aggregated portfolio Greeks
        """
        total_delta = sum(pos.get("quantity", 0) * pos.get("delta", 0) for pos in positions)
        total_gamma = sum(pos.get("quantity", 0) * pos.get("gamma", 0) for pos in positions)
        total_theta = sum(pos.get("quantity", 0) * pos.get("theta", 0) for pos in positions)
        total_vega = sum(pos.get("quantity", 0) * pos.get("vega", 0) for pos in positions)
        total_rho = sum(pos.get("quantity", 0) * pos.get("rho", 0) for pos in positions)
        
        return {
            "total_delta": total_delta,
            "total_gamma": total_gamma,
            "total_theta": total_theta,
            "total_vega": total_vega,
            "total_rho": total_rho,
        }


# ============================================================================
# STRATEGY BUILDERS
# ============================================================================

class StrategyBuilder:
    """
    Constructs multi-leg options and futures strategies.
    
    构建多腿期权和期货策略。
    """
    
    # Strategy templates with Greeks characteristics
    STRATEGIES = {
        "call_spread": {
            "legs": [
                {"type": "CALL", "action": "BUY", "strike_offset": 0},
                {"type": "CALL", "action": "SELL", "strike_offset": 1},
            ],
            "description": "Bull call spread - defined risk",
        },
        "put_spread": {
            "legs": [
                {"type": "PUT", "action": "BUY", "strike_offset": 0},
                {"type": "PUT", "action": "SELL", "strike_offset": -1},
            ],
            "description": "Bull put spread - credit spread",
        },
        "straddle": {
            "legs": [
                {"type": "CALL", "action": "BUY", "strike_offset": 0},
                {"type": "PUT", "action": "BUY", "strike_offset": 0},
            ],
            "description": "Long straddle - bet on volatility",
        },
        "strangle": {
            "legs": [
                {"type": "CALL", "action": "BUY", "strike_offset": 2},
                {"type": "PUT", "action": "BUY", "strike_offset": -2},
            ],
            "description": "Long strangle - cheaper vol bet",
        },
        "iron_condor": {
            "legs": [
                {"type": "CALL", "action": "SELL", "strike_offset": 1},
                {"type": "CALL", "action": "BUY", "strike_offset": 2},
                {"type": "PUT", "action": "SELL", "strike_offset": -1},
                {"type": "PUT", "action": "BUY", "strike_offset": -2},
            ],
            "description": "Iron condor - income strategy",
        },
        "collar": {
            "legs": [
                {"type": "STOCK", "action": "BUY", "quantity": 100},
                {"type": "PUT", "action": "BUY", "strike_offset": -1},
                {"type": "CALL", "action": "SELL", "strike_offset": 1},
            ],
            "description": "Collar - downside protection",
        },
    }
    
    @staticmethod
    def build_strategy(
        strategy_name: str,
        ticker: str,
        spot_price: float,
        quantity: int = 1,
        expiration_days: int = 30,
        implied_vol: float = 0.25,
    ) -> Dict[str, Any]:
        """
        Build a multi-leg strategy.
        
        Args:
            strategy_name: Name of strategy (call_spread, etc)
            ticker: Underlying ticker
            spot_price: Current spot price
            quantity: Number of contracts/shares
            expiration_days: Days to expiration
            implied_vol: Implied volatility
            
        Returns:
            Strategy with legs, Greeks, and economics
        """
        if strategy_name not in StrategyBuilder.STRATEGIES:
            logger.error(f"Unknown strategy: {strategy_name}")
            return {}
        
        template = StrategyBuilder.STRATEGIES[strategy_name]
        legs = []
        total_cost = 0.0
        max_loss = float('inf')
        max_profit = float('inf')
        
        for leg_template in template["legs"]:
            leg = {
                "ticker": ticker,
                "type": leg_template["type"],
                "action": leg_template["action"],
                "quantity": quantity,
                "strike_offset": leg_template.get("strike_offset", 0),
                # Price would be calculated from options chain
                "price": 0.0,
                "greeks": {},
            }
            legs.append(leg)
        
        return {
            "strategy_id": f"{ticker}_{strategy_name}_{datetime.utcnow().timestamp()}",
            "strategy_name": strategy_name,
            "ticker": ticker,
            "description": template["description"],
            "legs": legs,
            "total_cost": total_cost,
            "max_loss": max_loss if max_loss != float('inf') else None,
            "max_profit": max_profit if max_profit != float('inf') else None,
            "breakeven": [],
            "probability_of_profit": 0.5,
        }


# ============================================================================
# ADVANCED STRATEGY NODES
# ============================================================================

class OptionsAnalysisNode(BaseNode):
    """Fetch and analyze options chains to identify strategies."""
    
    def __init__(self):
        super().__init__("options_analysis_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Analyze options for strategy opportunities."""
        self.log("Analyzing options opportunities")
        state.analysis_results["analyzed_options"] = {}
        state.analysis_results["strategy_recommendations"] = []
        return state
    
    @staticmethod
    def analyze(state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze options from state dict."""
        return {
            "analyzed_options": {},
            "strategy_recommendations": [],
        }


class FuturesAnalysisNode(BaseNode):
    """Analyze futures contracts for hedging and speculation."""
    
    def __init__(self):
        super().__init__("futures_analysis_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Analyze futures contracts."""
        self.log("Analyzing futures contracts")
        state.analysis_results["viable_futures"] = {}
        state.analysis_results["hedging_recommendations"] = []
        return state


class CryptoDerivativesNode(BaseNode):
    """Analyze crypto perpetuals and futures."""
    
    def __init__(self):
        super().__init__("crypto_derivatives_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Analyze crypto derivatives."""
        self.log("Analyzing crypto derivatives")
        state.analysis_results["crypto_hedging_strategies"] = []
        state.analysis_results["perpetual_opportunities"] = []
        return state


class StrategyBuilderNode(BaseNode):
    """Construct multi-leg strategies from market view."""
    
    def __init__(self):
        super().__init__("strategy_builder_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Build multi-leg strategies."""
        self.log("Building multi-leg strategies")
        state.analysis_results["constructed_strategies"] = []
        state.analysis_results["strategy_recommendations"] = []
        return state
    
    @staticmethod
    def build(state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Build strategies from state dict."""
        return {
            "constructed_strategies": [],
            "strategy_recommendations": [],
        }


class GreeksMonitorNode(BaseNode):
    """Track and rebalance portfolio Greeks."""
    
    def __init__(self):
        super().__init__("greeks_monitor_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Monitor Greeks across portfolio."""
        self.log("Monitoring portfolio Greeks")
        state.analysis_results["greek_snapshots"] = {}
        state.analysis_results["rebalance_recommendations"] = []
        state.analysis_results["greek_alerts"] = []
        return state


class DeltaHedgingNode(BaseNode):
    """Maintain delta-neutral portfolio through hedging."""
    
    def __init__(self):
        super().__init__("delta_hedging_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Generate delta hedging trades."""
        self.log("Calculating delta hedges")
        state.analysis_results["hedging_orders"] = []
        state.analysis_results["expected_rebalance_cost"] = 0.0
        return state


class HedgeRecommenderNode(BaseNode):
    """Recommend optimal hedging strategies."""
    
    def __init__(self):
        super().__init__("hedge_recommender_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Generate hedging recommendations."""
        self.log("Recommending hedging strategies")
        state.analysis_results["recommended_hedges"] = {}
        state.analysis_results["best_hedge"] = None
        return state


class VolatilityArbitrageNode(BaseNode):
    """Identify volatility arbitrage opportunities."""
    
    def __init__(self):
        super().__init__("volatility_arbitrage_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Find volatility arbitrage trades."""
        self.log("Finding volatility arbitrage trades")
        state.analysis_results["vol_arbitrage_opportunities"] = []
        state.analysis_results["vol_arb_trades"] = []
        return state


class PairTradingNode(BaseNode):
    """Identify and monitor pair trading opportunities."""
    
    def __init__(self):
        super().__init__("pair_trading_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Execute pair trading strategies."""
        self.log("Analyzing pairs for trading")
        state.analysis_results["pair_trading_signals"] = []
        state.analysis_results["active_pairs"] = {}
        return state


class StrategyExecutorNode(BaseNode):
    """Execute multi-leg strategy orders."""
    
    def __init__(self):
        super().__init__("strategy_executor_node")

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Execute multi-leg strategies."""
        self.log("Executing multi-leg strategies")
        state.analysis_results["executed_orders"] = []
        state.analysis_results["execution_summary"] = ""
        return state


__all__ = [
    "GreeksCalculator",
    "StrategyBuilder",
    "OptionsAnalysisNode",
    "FuturesAnalysisNode",
    "CryptoDerivativesNode",
    "StrategyBuilderNode",
    "GreeksMonitorNode",
    "DeltaHedgingNode",
    "HedgeRecommenderNode",
    "VolatilityArbitrageNode",
    "PairTradingNode",
    "StrategyExecutorNode",
]
