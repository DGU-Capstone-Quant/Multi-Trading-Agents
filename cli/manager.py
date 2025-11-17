"""토론 실행 매니저"""
import os
from typing import List, Dict
from modules.context import Context


class DebateManager:
    def __init__(self, context: Context, date_ticker_map: Dict[str, List[str]]):
        self.context = context
        self.date_ticker_map = date_ticker_map
        self.sorted_dates = sorted(date_ticker_map.keys())
        self.current_date_index = 0

    def get_next_debate_items(self) -> List[Dict[str, str]]:
        if not self.sorted_dates:
            return []

        if self.current_date_index >= len(self.sorted_dates):
            self.current_date_index = 0

        current_date = self.sorted_dates[self.current_date_index]
        self.current_date_index += 1

        return [{"ticker": t, "trade_date": current_date} for t in self.date_ticker_map[current_date]]

    def run_debate(self, ticker: str, trade_date: str, rounds: int = 2) -> bool:
        if not os.getenv("RAPID_API_KEY") or not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("API 키가 설정되지 않았습니다.")

        self.context.set_cache(ticker=ticker, trade_date=trade_date, rounds=rounds)

        from graphs.debate.factory import create_debate_graph, _resolve_report_path, _read
        from graphs.trader.factory import create_trader_graph

        # market_report 로드 및 저장
        market_report = _read(_resolve_report_path(ticker, trade_date))
        self.context.set_report("market_report", market_report)
        self.context.set_report(f"{ticker}_{trade_date}_market_report", market_report)

        # Debate 실행
        create_debate_graph(self.context).run(self.context)
        self._save_report("investment_plan", ticker, trade_date)

        # Trader 실행
        create_trader_graph().run(self.context)
        self._save_cache("trader_decision", ticker, trade_date)
        self._save_cache("trader_recommendation", ticker, trade_date)

        self._add_completed_debate(ticker, trade_date)
        return True

    def _save_report(self, report_type: str, ticker: str, trade_date: str):
        content = self.context.get_report(report_type)
        if content:
            self.context.set_report(f"{ticker}_{trade_date}_{report_type}", content)

    def _save_cache(self, cache_key: str, ticker: str, trade_date: str):
        content = self.context.get_cache(cache_key, "")
        if content:
            self.context.set_cache(**{f"{ticker}_{trade_date}_{cache_key}": content})

    def _add_completed_debate(self, ticker: str, trade_date: str):
        debates = self.context.get_cache("completed_debates", [])
        if not any(d["ticker"] == ticker and d["trade_date"] == trade_date for d in debates):
            debates.append({"ticker": ticker, "trade_date": trade_date})
            debates.sort(key=lambda x: x["trade_date"], reverse=True)
            self.context.set_cache(completed_debates=debates)
