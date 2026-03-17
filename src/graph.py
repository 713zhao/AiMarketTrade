"""
Graph construction for deerflow multi-agent system.

This module defines the LangGraph state machine that orchestrates
the flow of data through various nodes. Phase 2 implements parallel
execution of analyst nodes before consensus aggregation.
"""

import asyncio
from typing import Dict, Any, TypedDict, List
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import DeerflowState, AnalystType, ConsensusSignal
from .nodes import (
    StockDataNode,
    TechnicalAnalystNode,
    FundamentalsAnalystNode,
    NewsAnalystNode,
    GrowthAnalystNode,
    MacroAnalystNode,
    RiskAnalystNode,
    ConsensusNode,
    DecisionNode,
    PortfolioRiskNode,
    PortfolioOptimizationNode,
    MacroScenarioNode,
    MultiScenarioAnalysisNode,
    RebalancingNode,
    # Phase 5 additions
    EfficientFrontierNode,
    PerformanceAttributionNode,
    TransactionCostNode,
    BacktestingEngineNode,
)
from .broker_integration import (
    # Phase 6 additions
    BrokerConnectorNode,
    TradeExecutorNode,
    OrderMonitorNode,
    PositionManagerNode,
    AccountMonitorNode,
    RiskControlNode,
    ComplianceLoggerNode,
)


class GraphConfig(TypedDict, total=False):
    """Configuration for graph construction."""
    checkpoint_dir: str
    enable_parallel: bool
    max_parallel: int
    analyst_weights: Dict[str, float]


def create_deerflow_graph(config: GraphConfig = None) -> StateGraph:
    """
    Create and configure the deerflow workflow graph.

    Phase 5 Architecture with Production Deployment & Real-Time Integration:

    stock_data_node
         |
         v
    +----+----+------------------+
    |         |                  |
    v         v                  v
    tech   fundamentals       news_analyst
    |         |                  |
    v         v                  |
    growth   macro               |
     |        |                  |
     +--------+                  |
              |                  |
              v                  v
            risk_analyst --> consensus_node
                                 |
                                 v
                         portfolio_risk_node
                                 |
                                 v
                       portfolio_optimization_node
                                 |
                       +---------+---------+
                       |                   |
                       v                   v
                macro_scenario_node  rebalancing_node
                       |                   |
                       +--------+----------+
                                |
                                v
                    multi_scenario_analysis_node
                                 |
                  +--+--+--+--+--+
                  |  |  |  |  |  |
                  v  v  v  v  v  v
            efficient_frontier  performance_attribution
            transaction_cost    backtesting_engine
                  |  |  |  |  |  |
                  +--+--+--+--+--+
                                |
                                v
                          decision_node --> END

    Phases 1-4 pipeline with Phase 5 production deployment:
    - Efficient frontier optimization with multiple portfolios
    - Performance attribution analysis
    - Transaction cost modeling and execution planning
    - Historical strategy validation via backtesting
    """
    if config is None:
        config = {}

    # Create the state graph
    workflow = StateGraph(DeerflowState)

    # Initialize nodes
    stock_data_node = StockDataNode()
    technical_analyst_node = TechnicalAnalystNode()
    fundamentals_analyst_node = FundamentalsAnalystNode()
    news_analyst_node = NewsAnalystNode()
    growth_analyst_node = GrowthAnalystNode()
    macro_analyst_node = MacroAnalystNode()
    risk_analyst_node = RiskAnalystNode()
    consensus_node = ConsensusNode()
    portfolio_risk_node = PortfolioRiskNode()
    portfolio_optimization_node = PortfolioOptimizationNode()
    macro_scenario_node = MacroScenarioNode()
    multi_scenario_analysis_node = MultiScenarioAnalysisNode()
    rebalancing_node = RebalancingNode()
    # Phase 5 nodes
    efficient_frontier_node = EfficientFrontierNode()
    performance_attribution_node = PerformanceAttributionNode()
    transaction_cost_node = TransactionCostNode()
    backtesting_engine_node = BacktestingEngineNode()
    # Phase 6 nodes
    broker_connector_node = BrokerConnectorNode()
    trade_executor_node = TradeExecutorNode()
    order_monitor_node = OrderMonitorNode()
    position_manager_node = PositionManagerNode()
    account_monitor_node = AccountMonitorNode()
    risk_control_node = RiskControlNode()
    compliance_logger_node = ComplianceLoggerNode()
    decision_node = DecisionNode()

    # Register nodes with the graph
    workflow.add_node("stock_data", stock_data_node.execute)
    workflow.add_node("technical_analyst", technical_analyst_node.execute)
    workflow.add_node("fundamentals_analyst", fundamentals_analyst_node.execute)
    workflow.add_node("news_analyst", news_analyst_node.execute)
    workflow.add_node("growth_analyst", growth_analyst_node.execute)
    workflow.add_node("macro_analyst", macro_analyst_node.execute)
    workflow.add_node("risk_analyst", risk_analyst_node.execute)
    workflow.add_node("consensus", consensus_node.execute)
    workflow.add_node("portfolio_risk", portfolio_risk_node.execute)
    workflow.add_node("portfolio_optimization", portfolio_optimization_node.execute)
    workflow.add_node("macro_scenario", macro_scenario_node.execute)
    workflow.add_node("multi_scenario_analysis", multi_scenario_analysis_node.execute)
    workflow.add_node("rebalancing", rebalancing_node.execute)
    # Phase 5 nodes
    workflow.add_node("efficient_frontier", efficient_frontier_node.execute)
    workflow.add_node("performance_attribution", performance_attribution_node.execute)
    workflow.add_node("transaction_cost", transaction_cost_node.execute)
    workflow.add_node("backtesting_engine", backtesting_engine_node.execute)
    # Phase 6 nodes
    workflow.add_node("broker_connector", broker_connector_node.execute)
    workflow.add_node("trade_executor", trade_executor_node.execute)
    workflow.add_node("order_monitor", order_monitor_node.execute)
    workflow.add_node("position_manager", position_manager_node.execute)
    workflow.add_node("account_monitor", account_monitor_node.execute)
    workflow.add_node("risk_control", risk_control_node.execute)
    workflow.add_node("compliance_logger", compliance_logger_node.execute)
    workflow.add_node("decision", decision_node.execute)

    # Parallel execution branch
    # After stock_data, all analyst nodes can run independently
    workflow.set_entry_point("stock_data")

    # Connect stock_data to all analyst nodes
    for analyst_node in [
        "technical_analyst",
        "fundamentals_analyst",
        "news_analyst",
        "growth_analyst",
        "macro_analyst",
        "risk_analyst",
    ]:
        workflow.add_edge("stock_data", analyst_node)

    # All analyst nodes converge to consensus
    for analyst_node in [
        "technical_analyst",
        "fundamentals_analyst",
        "news_analyst",
        "growth_analyst",
        "macro_analyst",
        "risk_analyst",
    ]:
        workflow.add_edge(analyst_node, "consensus")

    # Consensus leads to portfolio risk analysis (Phase 3)
    workflow.add_edge("consensus", "portfolio_risk")
    
    # Portfolio risk leads to portfolio optimization (Phase 3)
    workflow.add_edge("portfolio_risk", "portfolio_optimization")
    
    # Portfolio optimization branches to Phase 4 nodes
    workflow.add_edge("portfolio_optimization", "macro_scenario")
    workflow.add_edge("portfolio_optimization", "rebalancing")
    
    # Phase 4 nodes converge to multi-scenario analysis
    workflow.add_edge("macro_scenario", "multi_scenario_analysis")
    workflow.add_edge("rebalancing", "multi_scenario_analysis")
    
    # Phase 5: Multi-scenario analysis branches to all Phase 5 nodes
    workflow.add_edge("multi_scenario_analysis", "efficient_frontier")
    workflow.add_edge("multi_scenario_analysis", "performance_attribution")
    workflow.add_edge("multi_scenario_analysis", "transaction_cost")
    workflow.add_edge("multi_scenario_analysis", "backtesting_engine")
    
    # Phase 5 nodes converge to broker connector (Phase 6)
    workflow.add_edge("efficient_frontier", "broker_connector")
    workflow.add_edge("performance_attribution", "broker_connector")
    workflow.add_edge("transaction_cost", "broker_connector")
    workflow.add_edge("backtesting_engine", "broker_connector")
    
    # Phase 6: Broker connector establishes connections
    # Then branches to account monitor and risk control for pre-trade validation
    workflow.add_edge("broker_connector", "account_monitor")
    workflow.add_edge("broker_connector", "risk_control")
    
    # Risk control and account monitor lead to trade executor
    workflow.add_edge("risk_control", "trade_executor")
    workflow.add_edge("account_monitor", "trade_executor")
    
    # Trade executor monitors order status
    workflow.add_edge("trade_executor", "order_monitor")
    
    # Order monitor branches to position manager and compliance logger
    workflow.add_edge("order_monitor", "position_manager")
    workflow.add_edge("order_monitor", "compliance_logger")
    
    # Phase 6 nodes converge to final decision
    workflow.add_edge("position_manager", "decision")
    workflow.add_edge("compliance_logger", "decision")
    workflow.add_edge("decision", END)

    # Configure checkpointing
    memory_saver = MemorySaver()

    # Compile the graph
    compiled_graph = workflow.compile(
        checkpointer=memory_saver,
        interrupt_before=[],
        interrupt_after=[],
    )

    return compiled_graph


async def run_deerflow_graph(
    tickers: list[str],
    config: GraphConfig = None,
    initial_state: DeerflowState = None
) -> DeerflowState:
    """
    Execute the deerflow graph for a set of tickers.

    Args:
        tickers: List of stock ticker symbols to analyze
        config: Optional graph configuration (weights, parallel settings)
        initial_state: Optional pre-configured state

    Returns:
        Final DeerflowState with all results
    """
    from .state import DeerflowState
    from .config import get_settings
    import uuid

    settings = get_settings()

    # Create initial state if not provided
    if initial_state is None:
        initial_state = DeerflowState(
            session_id=str(uuid.uuid4()),
            tickers=tickers,
            analysis_scope={
                "time_horizon": settings.time_horizon,
                "risk_tolerance": settings.risk_tolerance,
                "max_position_size": settings.max_position_size,
            }
        )

    # Create the graph
    graph = create_deerflow_graph(config)

    print(f"[Graph] Starting deerflow analysis for {len(tickers)} tickers: {', '.join(tickers)}")
    if config and config.get('enable_parallel', True):
        print(f"[Graph] Parallel execution enabled for 6 analyst nodes")

    start_time = datetime.utcnow()

    try:
        # Execute the graph
        async for event in graph.astream(
            initial_state,
            config={
                "configurable": {
                    "thread_id": initial_state.session_id,
                }
            }
        ):
            # Log node transitions
            for node_name, node_state in event.items():
                if node_name != "__start__":
                    print(f"[Graph] Completed node: {node_name}")

        # Get final state
        final_state = graph.get_state({
            "configurable": {
                "thread_id": initial_state.session_id,
            }
        }).values

        # Calculate execution time
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        final_state.execution_time = execution_time

        print(f"[Graph] Analysis completed in {execution_time:.2f} seconds")
        print(f"[Graph] Data nodes: {len(final_state.ticker_data)} tickers")
        print(f"[Graph] Consensus signals: {len(final_state.consensus_signals)}")
        print(f"[Graph] Trading decisions: {len(final_state.trading_decisions)}")
        print(f"[Graph] Errors: {len(final_state.errors)}")

        return final_state

    except Exception as e:
        print(f"[Graph] Error during execution: {e}")
        import traceback
        traceback.print_exc()
        raise


def print_state_summary(state: DeerflowState) -> None:
    """Print a human-readable summary of the analysis results."""
    print("\n" + "="*80)
    print("DEERFLOW ANALYSIS SUMMARY")
    print("="*80)

    print(f"\nSession ID: {state.session_id}")
    print(f"Tickers Analyzed: {', '.join(state.tickers)}")
    print(f"Execution Time: {state.execution_time:.2f}s" if state.execution_time else "Execution Time: N/A")
    print(f"API Calls Made: {state.api_calls}")
    print(f"Cache Hits: {state.cache_hits}")

    print("\n" + "-"*80)
    print("ANALYSIS RESULTS BY TICKER")
    print("-"*80)

    for ticker in state.tickers:
        print(f"\n{ticker}:")
        ticker_data = state.ticker_data.get(ticker)
        if ticker_data:
            print(f"  Data Quality: {ticker_data.data_quality_score:.1%}")
            print(f"  Provider: {ticker_data.provider}")

        # Technical analysis
        tech = state.technical_analyses.get(ticker)
        if tech:
            print(f"  Technical: Trend={tech.trend}, Momentum={tech.momentum}, Confidence={tech.confidence:.1%}")
            if tech.signals:
                buys = len([s for s in tech.signals if s['signal'] == 'buy'])
                sells = len([s for s in tech.signals if s['signal'] == 'sell'])
                print(f"    Signals: {buys} buy, {sells} sell")

        # Fundamental analysis
        fund = state.fundamental_analyses.get(ticker)
        if fund:
            print(f"  Fundamental: Valuation={fund.valuation}, PE={fund.pe_ratio:.1f if fund.pe_ratio else 'N/A'}, ROE={fund.roe:.1f if fund.roe else 'N/A'}%")

        # News analysis
        news = state.news_analyses.get(ticker)
        if news:
            print(f"  News: Sentiment={news.overall_sentiment:.2f}, Volume={news.news_volume} articles, Recent={news.recent_news_count}")

        # Growth analysis
        growth = state.growth_analyses.get(ticker)
        if growth:
            print(f"  Growth: Score={growth.growth_score:.1f}/100, Revenue Growth={growth.revenue_growth_rate:.1f if growth.revenue_growth_rate else 'N/A'}%")

        # Risk analysis
        risk = state.risk_analyses.get(ticker)
        if risk:
            print(f"  Risk: Level={risk.risk_level}, Score={risk.risk_score:.1f}/100, Volatility={risk.volatility:.1%}")

        # Macro analysis
        macro = state.macro_analyses.get(ticker)
        if macro:
            print(f"  Macro: Score={macro.macro_score:.1f}/100, Sector={macro.sector}")

        # Consensus
        consensus = state.consensus_signals.get(ticker)
        if consensus:
            print(f"  Consensus: {consensus.overall_signal.value.upper()} (strength: {consensus.signal_strength:.1%})")
            print(f"    Confidence: {consensus.consensus_confidence:.1%}")
            if consensus.target_price:
                print(f"    Target Price: ${consensus.target_price:.2f}")

        # Trading decision
        decision = state.trading_decisions.get(ticker)
        if decision:
            print(f"  Decision: {decision.action.value.upper()} - {decision.position_size:.1f}% position")
            if decision.stop_loss:
                print(f"    Stop: ${decision.stop_loss:.2f}, Target: ${decision.take_profit:.2f if decision.take_profit else 'N/A'}")
            print(f"    Rationale: {decision.rationale[:120]}..." if len(decision.rationale) > 120 else f"    Rationale: {decision.rationale}")

    print("\n" + "="*80)

    if state.errors:
        print(f"\nERRORS ({len(state.errors)} nodes with errors):")
        for node, errors in state.errors.items():
            print(f"  {node}: {len(errors)} error(s)")
            for err in errors[:3]:  # Show first 3 errors per node
                if err.get('ticker'):
                    print(f"    - {err['ticker']}: {err['error'][:80]}")
                else:
                    print(f"    - {err['error'][:80]}")
            if len(errors) > 3:
                print(f"    ... and {len(errors)-3} more")

    print("="*80 + "\n")


# Mock data provider for testing when API keys are not available
class MockStockDataNode(StockDataNode):
    """Mock data node that generates synthetic data for testing."""

    async def _fetch_ticker_data(self, ticker: str, provider: str):
        """Generate mock data for testing."""
        import numpy as np
        import pandas as pd
        from .state import TickerData, DataProvider

        # Generate synthetic price data
        n_days = 500
        dates = pd.date_range(end=datetime.utcnow(), periods=n_days, freq='D')
        # Use different seeds per ticker for variety
        seed = hash(ticker) % 10000
        np.random.seed(seed)
        returns = np.random.normal(0.0005, 0.015, n_days)
        prices = 100 * np.exp(np.cumsum(returns))

        mock_data = {
            'date': dates.strftime('%Y-%m-%d').tolist(),
            'open': prices * (1 + np.random.uniform(-0.005, 0.005, n_days)).tolist(),
            'high': prices * (1 + np.random.uniform(0, 0.01, n_days)).tolist(),
            'low': prices * (1 + np.random.uniform(-0.01, 0, n_days)).tolist(),
            'close': prices.tolist(),
            'volume': np.random.randint(100000, 10000000, n_days).tolist(),
        }

        # Generate mock fundamentals
        sectors = ['Technology', 'Healthcare', 'Finance', 'Consumer', 'Energy']
        sector = sectors[seed % len(sectors)]

        return TickerData(
            ticker=ticker,
            provider=DataProvider.YAHOO,
            historical_data=mock_data,
            company_info={
                "name": f"{ticker} Inc.",
                "sector": sector,
                "industry": sector + " Sector",
                "country": "USA",
            },
            key_metrics={
                "pe_ratio": np.random.uniform(10, 30),
                "pb_ratio": np.random.uniform(1, 5),
                "roe": np.random.uniform(5, 25),
                "revenue_growth": np.random.uniform(-5, 25),
                "debt_to_equity": np.random.uniform(0.2, 2.0),
                "current_ratio": np.random.uniform(0.8, 3.0),
            },
            financial_statements={
                "income": {
                    "revenue": np.random.uniform(1e9, 1e11),
                    "net_income": np.random.uniform(1e8, 1e10),
                },
                "balance": {
                    "total_assets": np.random.uniform(1e9, 1e11),
                    "total_liabilities": np.random.uniform(5e8, 5e10),
                },
                "cashflow": {
                    "free_cash_flow": np.random.uniform(1e8, 1e10),
                },
            },
            news=[],  # Mock news would be generated if needed
            data_quality_score=0.95,
        )


def create_mock_graph() -> StateGraph:
    """
    Create a graph with mock data nodes for testing without API keys.
    
    Uses MockStockDataNode to generate synthetic data, but all
    analyst nodes are real implementations. Includes Phase 3-5 portfolio analysis.
    """
    workflow = StateGraph(DeerflowState)

    # Use mock data node
    stock_data_node = MockStockDataNode()
    technical_analyst_node = TechnicalAnalystNode()
    fundamentals_analyst_node = FundamentalsAnalystNode()
    news_analyst_node = NewsAnalystNode()
    growth_analyst_node = GrowthAnalystNode()
    macro_analyst_node = MacroAnalystNode()
    risk_analyst_node = RiskAnalystNode()
    consensus_node = ConsensusNode()
    portfolio_risk_node = PortfolioRiskNode()
    portfolio_optimization_node = PortfolioOptimizationNode()
    macro_scenario_node = MacroScenarioNode()
    multi_scenario_analysis_node = MultiScenarioAnalysisNode()
    rebalancing_node = RebalancingNode()
    # Phase 5 nodes
    efficient_frontier_node = EfficientFrontierNode()
    performance_attribution_node = PerformanceAttributionNode()
    transaction_cost_node = TransactionCostNode()
    backtesting_engine_node = BacktestingEngineNode()
    decision_node = DecisionNode()

    workflow.add_node("stock_data", stock_data_node.execute)
    workflow.add_node("technical_analyst", technical_analyst_node.execute)
    workflow.add_node("fundamentals_analyst", fundamentals_analyst_node.execute)
    workflow.add_node("news_analyst", news_analyst_node.execute)
    workflow.add_node("growth_analyst", growth_analyst_node.execute)
    workflow.add_node("macro_analyst", macro_analyst_node.execute)
    workflow.add_node("risk_analyst", risk_analyst_node.execute)
    workflow.add_node("consensus", consensus_node.execute)
    workflow.add_node("portfolio_risk", portfolio_risk_node.execute)
    workflow.add_node("portfolio_optimization", portfolio_optimization_node.execute)
    workflow.add_node("macro_scenario", macro_scenario_node.execute)
    workflow.add_node("multi_scenario_analysis", multi_scenario_analysis_node.execute)
    workflow.add_node("rebalancing", rebalancing_node.execute)
    # Phase 5 nodes
    workflow.add_node("efficient_frontier", efficient_frontier_node.execute)
    workflow.add_node("performance_attribution", performance_attribution_node.execute)
    workflow.add_node("transaction_cost", transaction_cost_node.execute)
    workflow.add_node("backtesting_engine", backtesting_engine_node.execute)
    workflow.add_node("decision", decision_node.execute)

    # Parallel structure: stock_data → all analysts → consensus → portfolio_risk → portfolio_optimization → [macro_scenario, rebalancing] → multi_scenario_analysis → [phase5_nodes] → decision
    workflow.set_entry_point("stock_data")

    analyst_nodes = [
        "technical_analyst",
        "fundamentals_analyst",
        "news_analyst",
        "growth_analyst",
        "macro_analyst",
        "risk_analyst",
    ]

    for node in analyst_nodes:
        workflow.add_edge("stock_data", node)
        workflow.add_edge(node, "consensus")

    workflow.add_edge("consensus", "portfolio_risk")
    workflow.add_edge("portfolio_risk", "portfolio_optimization")
    workflow.add_edge("portfolio_optimization", "macro_scenario")
    workflow.add_edge("portfolio_optimization", "rebalancing")
    workflow.add_edge("macro_scenario", "multi_scenario_analysis")
    workflow.add_edge("rebalancing", "multi_scenario_analysis")
    # Phase 5 branches
    workflow.add_edge("multi_scenario_analysis", "efficient_frontier")
    workflow.add_edge("multi_scenario_analysis", "performance_attribution")
    workflow.add_edge("multi_scenario_analysis", "transaction_cost")
    workflow.add_edge("multi_scenario_analysis", "backtesting_engine")
    # Phase 5 converges to decision
    workflow.add_edge("efficient_frontier", "decision")
    workflow.add_edge("performance_attribution", "decision")
    workflow.add_edge("transaction_cost", "decision")
    workflow.add_edge("backtesting_engine", "decision")
    workflow.add_edge("decision", END)

    memory_saver = MemorySaver()
    return workflow.compile(checkpointer=memory_saver)


def create_simplified_graph(analyst_types: List[AnalystType] = None) -> StateGraph:
    """
    Create a graph with only selected analyst nodes.
    
    Useful for testing specific analysts or for environments where
    some data sources are unavailable. Includes Phase 3-4 portfolio analysis.
    
    Args:
        analyst_types: List of analyst types to include. If None, includes all.
    """
    workflow = StateGraph(DeerflowState)

    # Always include these
    stock_data_node = StockDataNode()
    consensus_node = ConsensusNode()
    portfolio_risk_node = PortfolioRiskNode()
    portfolio_optimization_node = PortfolioOptimizationNode()
    macro_scenario_node = MacroScenarioNode()
    multi_scenario_analysis_node = MultiScenarioAnalysisNode()
    rebalancing_node = RebalancingNode()
    # Phase 5 nodes
    efficient_frontier_node = EfficientFrontierNode()
    performance_attribution_node = PerformanceAttributionNode()
    transaction_cost_node = TransactionCostNode()
    backtesting_engine_node = BacktestingEngineNode()
    decision_node = DecisionNode()

    workflow.add_node("stock_data", stock_data_node.execute)
    workflow.add_node("consensus", consensus_node.execute)
    workflow.add_node("portfolio_risk", portfolio_risk_node.execute)
    workflow.add_node("portfolio_optimization", portfolio_optimization_node.execute)
    workflow.add_node("macro_scenario", macro_scenario_node.execute)
    workflow.add_node("multi_scenario_analysis", multi_scenario_analysis_node.execute)
    workflow.add_node("rebalancing", rebalancing_node.execute)
    # Phase 5 nodes
    workflow.add_node("efficient_frontier", efficient_frontier_node.execute)
    workflow.add_node("performance_attribution", performance_attribution_node.execute)
    workflow.add_node("transaction_cost", transaction_cost_node.execute)
    workflow.add_node("backtesting_engine", backtesting_engine_node.execute)
    workflow.add_node("decision", decision_node.execute)

    # Map analyst type to node
    analyst_node_map = {
        AnalystType.TECHNICAL: TechnicalAnalystNode(),
        AnalystType.FUNDAMENTALS: FundamentalsAnalystNode(),
        AnalystType.NEWS: NewsAnalystNode(),
        AnalystType.GROWTH: GrowthAnalystNode(),
        AnalystType.MACRO: MacroAnalystNode(),
        AnalystType.RISK: RiskAnalystNode(),
    }

    # Select which analysts to include
    if analyst_types is None:
        analyst_types = list(analyst_node_map.keys())

    selected_nodes = []
    for at in analyst_types:
        if at in analyst_node_map:
            node = analyst_node_map[at]
            node_name = f"{at.value}_analyst"
            workflow.add_node(node_name, node.execute)
            selected_nodes.append(node_name)

    # Build graph
    workflow.set_entry_point("stock_data")

    for node_name in selected_nodes:
        workflow.add_edge("stock_data", node_name)
        workflow.add_edge(node_name, "consensus")

    workflow.add_edge("consensus", "portfolio_risk")
    workflow.add_edge("portfolio_risk", "portfolio_optimization")
    workflow.add_edge("portfolio_optimization", "macro_scenario")
    workflow.add_edge("portfolio_optimization", "rebalancing")
    workflow.add_edge("macro_scenario", "multi_scenario_analysis")
    workflow.add_edge("rebalancing", "multi_scenario_analysis")
    # Phase 5 branches
    workflow.add_edge("multi_scenario_analysis", "efficient_frontier")
    workflow.add_edge("multi_scenario_analysis", "performance_attribution")
    workflow.add_edge("multi_scenario_analysis", "transaction_cost")
    workflow.add_edge("multi_scenario_analysis", "backtesting_engine")
    # Phase 5 converges to decision
    workflow.add_edge("efficient_frontier", "decision")
    workflow.add_edge("performance_attribution", "decision")
    workflow.add_edge("transaction_cost", "decision")
    workflow.add_edge("backtesting_engine", "decision")
    workflow.add_edge("decision", END)

    memory_saver = MemorySaver()
    return workflow.compile(checkpointer=memory_saver)
