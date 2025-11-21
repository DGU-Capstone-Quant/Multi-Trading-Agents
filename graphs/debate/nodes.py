# graphs/debate/nodes.py

from datetime import datetime
from pathlib import Path
import json

from modules.graph.node import BaseNode
from graphs.debate.agents import BullResearcher, BearResearcher, ResearchManager
from modules.context import Context

LOG_DIR = Path("logs/research_dialogs")


def _write_json(path: Path, payload: dict):
    """JSON 파일을 저장하는 헬퍼 함수"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _round_dir(context: Context) -> Path:
    """로그 디렉토리 경로를 생성하는 함수"""
    tkr = context.get_cache("ticker", "UNKNOWN")
    date = context.get_config("trade_date", "") or context.get_cache("date", "UNKNOWN_DATE")
    return LOG_DIR / f"{tkr}_{date}"


class DebateSelectionNode(BaseNode):
    """
    여러 ticker에 대해 순차적으로 토론을 진행하기 위한 Selection Node
    analyst의 SelectionNode 패턴을 따름
    """
    def __init__(self, name: str):
        super().__init__(name)

    def run(self, context: Context) -> Context:
        # cache에서 먼저 tickers를 가져오고 (main_screen에서 설정), 없으면 recommendation 사용
        tickers = context.get_cache('tickers', [])
        if not tickers:
            tickers = context.get_cache("recommendation", [])
        if not tickers:
            tickers = context.get_config('tickers', [])

        if not tickers:
            raise ValueError("No tickers available for analysis.")

        # tickers를 cache에 저장 (다른 노드에서 사용)
        context.set_cache(tickers=list(tickers))

        # config의 trade_date를 cache의 date로도 설정 (다른 노드에서 사용)
        trade_date = context.get_config("trade_date", "")
        if trade_date:
            context.set_cache(date=trade_date)

        # 선택된 ticker로 토론 초기화
        context.set_cache(
            ticker=tickers[0],
            tickers=list(tickers[1:]),
            history="",  # 전체 토론 히스토리
            bull_history="",  # Bull 전용 히스토리
            bear_history="",  # Bear 전용 히스토리
            current_response="",  # 가장 최근 발언
            count=0,  # 토론 카운트
        )

        self.state = 'passed'

        return context


class BullNode(BaseNode):
    """Bull 에이전트를 실행하는 노드"""

    def __init__(self, name: str = "Bull"):
        super().__init__(name)
        self.agent = BullResearcher(name=f"{name} Analyst")

    def run(self, context: Context) -> Context:
        # Bull 에이전트 실행
        context = self.agent.run(context)
        self.state = 'passed'

        # 토론 로그를 JSON 파일로 저장
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            _write_json(
                _round_dir(context) / f"bull_round_{context.get_cache('count',0)}_{ts}.json",
                {
                    "time": datetime.now().isoformat(),
                    "history_tail": context.get_cache("current_response", ""),
                    "count": context.get_cache("count", 0),
                },
            )
        except Exception as e:
            print("[BullNode][log]", e)

        return context


class BearNode(BaseNode):
    """Bear 에이전트를 실행하는 노드"""

    def __init__(self, name: str = "Bear"):
        super().__init__(name)
        self.agent = BearResearcher(name=f"{name} Analyst")

    def run(self, context: Context) -> Context:
        # Bear 에이전트 실행
        context = self.agent.run(context)
        self.state = 'passed'

        # 토론 로그를 JSON 파일로 저장
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            _write_json(
                _round_dir(context) / f"bear_round_{context.get_cache('count',0)}_{ts}.json",
                {
                    "time": datetime.now().isoformat(),
                    "history_tail": context.get_cache("current_response", ""),
                    "count": context.get_cache("count", 0),
                },
            )
        except Exception as e:
            print("[BearNode][log]", e)

        return context


class ManagerNode(BaseNode):
    """Manager 에이전트를 실행하는 노드"""

    def __init__(self, name: str = "Manager"):
        super().__init__(name)
        self.agent = ResearchManager(name=f"{name} Manager")

    def run(self, context: Context) -> Context:
        # Manager 에이전트 실행
        context = self.agent.run(context)
        self.state = 'passed'

        # 매니저 결정을 JSON 로그 파일로 저장
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            _write_json(
                _round_dir(context) / f"manager_decision_{ts}.json",
                {
                    "time": datetime.now().isoformat(),
                    "decision": context.get_cache("manager_decision")
                },
            )
        except Exception as e:
            print("[ManagerNode][log]", e)

        # 투자 계획을 Context에 저장
        try:
            plan = context.get_cache("manager_decision") or {}
            ticker = context.get_cache("ticker", "UNKNOWN")
            raw_date = context.get_config("trade_date", "") or context.get_cache("date", "UNKNOWN_DATE")
            # YYYY-MM-DD → YYYYMMDDTHHMM 변환
            if raw_date and "-" in raw_date:
                date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y%m%dT%H%M")
            else:
                date = raw_date

            # 마크다운 내용 구성
            md = [
                f"# Investment Plan ({ticker} / {date})",
                "",
                f"**Decision:** {plan.get('decision','')}",
                "",
                "## Rationale",
                plan.get("rationale", ""),
                "",
                "## Plan",
                plan.get("plan", ""),
            ]

            # Context의 reports에 저장
            context.set_report(ticker, date, "investment_plan", "\n".join(md))

            # 테스트: 모든 결정(BUY, HOLD, SELL)을 portfolio에 추가, 추후 Trader로 옮길 예정
            portfolio = context.get_cache("portfolio", {}) or {}
            trade_date = context.get_config("trade_date", date)
            # 거래 내역을 리스트로 저장 (여러 날짜의 거래 기록)
            if ticker not in portfolio:
                portfolio[ticker] = []
            portfolio[ticker].append({"added_at": trade_date, "decision": plan.get("decision", "")})
            context.set_cache(portfolio=portfolio)

        except Exception as e:
            print("[ManagerNode][save plan]", e)

        return context
    