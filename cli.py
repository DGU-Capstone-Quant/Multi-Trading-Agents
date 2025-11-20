#!/usr/bin/env python3
"""멀티 트레이딩 에이전트 대시보드 CLI"""

from datetime import datetime, timedelta
from modules.context import Context
from cli import TradingDashboardApp


def main():
    """트레이딩 대시보드 CLI 진입점"""
    context = Context()
    context.set_config(
        analysis_tasks=["financial",],
        tickers=["AAPL",],
        max_portfolio_size=1,
        rounds=2,
    )

    # 기본 날짜/종목 맵 생성 (최근 5 거래일)
    date_ticker_map = {}
    base_date = datetime.now()
    tickers = ["AAPL", "GOOGL", "MSFT"]

    for i in range(5):
        trade_date = (base_date - timedelta(days=i)).strftime("%Y-%m-%d")
        date_ticker_map[trade_date] = tickers

    # Context 초기화
    context.set_cache(portfolio={}, completed_debates=[], trade_progress_keys=[])

    # 앱 실행
    app = TradingDashboardApp(context, date_ticker_map)
    app.run()


if __name__ == "__main__":
    main()
