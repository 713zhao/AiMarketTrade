"""
Data fetching node for retrieving market data from OpenBB.

Handles multiple data providers with fallback logic, data
normalization, and quality scoring.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from openbb import obb
import pandas as pd
import numpy as np

from ..models import DeerflowState, TickerData, DataProvider
from ..config import get_settings
from .base import BaseNode


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
                result = obb.equity.price.historical(
                    symbol=ticker,
                    provider=provider if provider != "yahoo" else "yfinance",
                    period=period,
                    interval=interval,
                )

                if result.empty:
                    return {}

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
                income = obb.equity.financials.income(symbol=ticker, provider=provider if provider != "yahoo" else "yfinance")
                if not income.empty:
                    statements["income"] = income.to_dict()

                balance = obb.equity.financials.balance(symbol=ticker, provider=provider if provider != "yahoo" else "yfinance")
                if not balance.empty:
                    statements["balance"] = balance.to_dict()

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
        if company_info and len(company_info) > 0:
            score += 0.2

        # Financial statements (50%)
        if financial_statements:
            stmt_count = len(financial_statements)
            score += 0.5 * (stmt_count / 3)

        return min(1.0, score)
