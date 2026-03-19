"""
Integration module for connecting trading simulation with AnalysisEngine.
"""

import logging
from typing import List, Optional
from .trading_simulator import TradingSimulator


class TradingIntegration:
    """
    Integrates trading simulation with AnalysisEngine.
    
    Responsibilities:
    - Subscribe to AnalysisEngine recommendations
    - Process recommendations through trading simulator
    - Log trade execution results
    """
    
    def __init__(self, trading_simulator: TradingSimulator, analysis_engine=None):
        """
        Initialize Trading Integration.
        
        Args:
            trading_simulator: TradingSimulator instance
            analysis_engine: Optional AnalysisEngine instance
        """
        self.trading_simulator = trading_simulator
        self.analysis_engine = analysis_engine
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Trading Integration initialized")
    
    def process_analysis_results(
        self,
        portfolio_id: str,
        recommendations: List
    ) -> List:
        """
        Processes recommendations from AnalysisEngine.
        
        Args:
            portfolio_id: Portfolio ID to execute trades for
            recommendations: List of StockRecommendation objects
            
        Returns:
            List of executed Trade objects
        """
        executed_trades = []
        
        self.logger.info(f"Processing {len(recommendations)} recommendations for portfolio {portfolio_id}")
        
        for recommendation in recommendations:
            try:
                trade = self.trading_simulator.process_recommendation(
                    portfolio_id,
                    recommendation
                )
                
                if trade:
                    executed_trades.append(trade)
                    self.logger.info(
                        f"Executed trade: {trade.action.value} {trade.quantity} "
                        f"{trade.symbol} @ ${trade.price}"
                    )
                
            except Exception as e:
                self.logger.error(
                    f"Failed to process recommendation for {recommendation.symbol}: {e}"
                )
        
        self.logger.info(
            f"Processed {len(recommendations)} recommendations, "
            f"executed {len(executed_trades)} trades"
        )
        
        return executed_trades
