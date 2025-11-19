#!/usr/bin/env python3
"""
cli/base.py: 추상 클래스
cli/screens.py: 모든 화면 클래스
cli/widgets.py: 모든 위젯 클래스
cli/manager.py: 토론과 거래 관리자
cli/loader.py: 데이터 로더 유틸리티
cli/app.py: 메인 애플리케이션
"""

from modules.context import Context
from cli import TradingDashboardApp, scan_date_ticker_map


def main():
    """트레이딩 대시보드 CLI 진입점"""
    context = Context()

    date_ticker_map = scan_date_ticker_map()

    if not date_ticker_map:
        print("results 폴더에 데이터가 없습니다")
        return

    # 포트폴리오 추출
    all_tickers = set()
    for tickers in date_ticker_map.values():
        all_tickers.update(tickers)

    # Context에 포트폴리오 저장
    context.set_cache(
        portfolio=sorted(list(all_tickers)),
        completed_debates=[]
    )

    # 앱 실행
    app = TradingDashboardApp(context, date_ticker_map)
    app.run()


if __name__ == "__main__":
    main()
