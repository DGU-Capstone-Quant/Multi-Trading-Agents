"""토론 실행 매니저 모듈"""

import os
from typing import List, Dict

from modules.context import Context


class DebateManager:
    """자동 토론 실행 관리자"""

    def __init__(self, context: Context, date_ticker_map: Dict[str, List[str]]):
        self.context = context
        self.date_ticker_map = date_ticker_map
        self.sorted_dates = sorted(date_ticker_map.keys())
        self.current_date_index = 0

    def get_next_debate_items(self) -> List[Dict[str, str]]:
        """
        다음 토론 대상 가져오기
        """
        if not self.sorted_dates:
            return []

        # 모든 trade_date를 다 처리했으면 처음으로 돌아감
        if self.current_date_index >= len(self.sorted_dates):
            self.current_date_index = 0

        # 현재 trade_date
        current_trade_date = self.sorted_dates[self.current_date_index]

        # 현재 trade_date의 모든 ticker
        tickers = self.date_ticker_map[current_trade_date]

        # 다음 trade_date로 이동
        self.current_date_index += 1

        # 모든 ticker에 대한 토론 항목 생성
        return [
            {"ticker": ticker, "trade_date": current_trade_date}
            for ticker in tickers
        ]

    def run_debate(self, ticker: str, trade_date: str, rounds: int = 2) -> bool:
        """
        토론 실행
        """
        try:
            # API 키 확인
            if not os.getenv("RAPID_API_KEY"):
                raise ValueError("RAPID_API_KEY가 설정되지 않았습니다.")

            if not os.getenv("GOOGLE_API_KEY"):
                raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")

            # Context에 필요한 정보 설정
            self.context.set_cache(
                ticker=ticker,
                trade_date=trade_date,
                rounds=rounds
            )

            # Debate Graph 실행
            from graphs.debate.factory import create_debate_graph, _resolve_report_path, _read

            # market_report 로드
            rp = _resolve_report_path(ticker, trade_date)
            self.context.set_report("market_report", _read(rp))

            debate_graph = create_debate_graph(self.context)
            debate_graph.run(self.context)

            # Trader Graph 실행
            from graphs.trader.factory import create_trader_graph

            trader_graph = create_trader_graph()
            trader_graph.run(self.context)

            # 완료된 토론에 추가
            self._add_completed_debate(ticker, trade_date)

            return True

        except Exception:
            raise

    def _add_completed_debate(self, ticker: str, trade_date: str) -> None:
        """완료된 토론에 추가"""
        completed_debates = self.context.get_cache("completed_debates", [])
        if not any(d["ticker"] == ticker and d["trade_date"] == trade_date for d in completed_debates):
            completed_debates.append({"ticker": ticker, "trade_date": trade_date})
            completed_debates.sort(key=lambda x: x["trade_date"], reverse=True)
            self.context.set_cache(completed_debates=completed_debates)
