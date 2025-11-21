#!/usr/bin/env python3
"""멀티 트레이딩 에이전트 대시보드 CLI"""

from modules.context import Context
from cli import TradingDashboardApp


def main():
    """트레이딩 대시보드 CLI 진입점"""
    context = Context()
    context.set_config(
        analysis_tasks=["financial",],
        max_portfolio_size=1,
        rounds=2,
    )

    # Context 초기화
    context.set_cache(portfolio={}, completed_debates=[], trade_progress_keys=[])

    # 앱 실행
    app = TradingDashboardApp(context)
    app.run()


if __name__ == "__main__":
    main()
