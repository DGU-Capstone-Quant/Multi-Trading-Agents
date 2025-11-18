"""토론 실행 관리자"""
import os
from typing import List, Dict, Callable, Optional
from modules.context import Context


class DebateManager:
    """토론 및 트레이딩 프로세스 관리자"""

    def __init__(self, context: Context, date_ticker_map: Dict[str, List[str]]):
        self.context = context
        self.date_ticker_map = date_ticker_map
        self.sorted_dates = sorted(date_ticker_map.keys())
        self.current_date_index = 0

    def get_next_debate_items(self) -> List[Dict[str, str]]:
        """다음 토론 항목 가져오기 (날짜별 순환)"""
        if not self.sorted_dates:
            return []

        if self.current_date_index >= len(self.sorted_dates):
            self.current_date_index = 0

        current_date = self.sorted_dates[self.current_date_index]
        self.current_date_index += 1

        return [{"ticker": t, "trade_date": current_date} for t in self.date_ticker_map[current_date]]

    def run_debate(
        self,
        ticker: str,
        trade_date: str,
        rounds: int = 2,
        progress_callback: Optional[Callable[[str, Dict[str, str]], None]] = None
    ) -> bool:
        """토론 및 트레이더 실행"""
        if not os.getenv("RAPID_API_KEY") or not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("API 키가 설정되지 않았습니다")

        # Context에 기본 정보 설정
        self.context.set_cache(ticker=ticker, trade_date=trade_date, rounds=rounds)

        from graphs.debate.factory import create_debate_graph, _resolve_report_path, _read
        from graphs.trader.factory import create_trader_graph

        # market_report 로드
        market_report = _read(_resolve_report_path(ticker, trade_date))
        self.context.set_report("market_report", market_report)
        self.context.set_report(f"{ticker}_{trade_date}_market_report", market_report)

        # Debate 그래프 실행
        create_debate_graph(self.context).run(self.context)
        self._save_report("investment_plan", ticker, trade_date)

        # investment_plan 준비 완료 알림
        plan_content = self.context.get_report(f"{ticker}_{trade_date}_investment_plan") or ""
        self._notify_progress(progress_callback, "investment_plan_ready", {
            "ticker": ticker,
            "trade_date": trade_date,
            "plan": plan_content,
        })

        # Trader 그래프 실행
        create_trader_graph().run(self.context)
        self._save_cache("trader_decision", ticker, trade_date)
        self._save_cache("trader_recommendation", ticker, trade_date)

        # trader 완료 알림
        decision = self.context.get_cache(f"{ticker}_{trade_date}_trader_decision", "")
        recommendation = self.context.get_cache(f"{ticker}_{trade_date}_trader_recommendation", "")
        self._notify_progress(progress_callback, "trader_finished", {
            "ticker": ticker,
            "trade_date": trade_date,
            "decision": decision,
            "recommendation": recommendation,
        })

        self._add_completed_debate(ticker, trade_date)
        return True

    def _save_report(self, report_type: str, ticker: str, trade_date: str):
        """보고서를 ticker_trade_date 형식으로 저장"""
        content = self.context.get_report(report_type)
        if content:
            self.context.set_report(f"{ticker}_{trade_date}_{report_type}", content)

    def _save_cache(self, cache_key: str, ticker: str, trade_date: str):
        """캐시를 ticker_trade_date 형식으로 저장"""
        content = self.context.get_cache(cache_key, "")
        if content:
            self.context.set_cache(**{f"{ticker}_{trade_date}_{cache_key}": content})

    def _add_completed_debate(self, ticker: str, trade_date: str):
        """완료된 토론 목록에 추가"""
        debates = self.context.get_cache("completed_debates", [])
        if not any(d["ticker"] == ticker and d["trade_date"] == trade_date for d in debates):
            debates.append({"ticker": ticker, "trade_date": trade_date})
            debates.sort(key=lambda x: x["trade_date"], reverse=True)
            self.context.set_cache(completed_debates=debates)

    def _notify_progress(
        self,
        callback: Optional[Callable[[str, Dict[str, str]], None]],
        event: str,
        payload: Dict[str, str],
    ) -> None:
        """진행 상황 콜백 호출"""
        if callback:
            try:
                callback(event, payload)
            except Exception:
                pass
