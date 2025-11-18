# graphs/debate/nodes.py

from datetime import datetime
from pathlib import Path
import json

from modules.graph.node import BaseNode
from graphs.debate.agents import BullResearcher, BearResearcher, ResearchManager
from modules.context import Context

LOG_DIR = Path("logs/research_dialogs")  # 토론 로그가 저장될 디렉토리
RESULTS_DIR = Path("results")  # 최종 결과가 저장될 디렉토리

# 유틸리티 함수
def _write_json(path: Path, payload: dict):  # JSON 파일을 저장하는 헬퍼 함수
    path.parent.mkdir(parents=True, exist_ok=True)  # 부모 디렉토리가 없으면 생성
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")  # JSON 저장

def _round_dir(context: Context) -> Path:  # 로그 디렉토리 경로를 생성하는 함수
    tkr = context.get_cache("ticker", "UNKNOWN")  # 티커 심볼
    dt = context.get_cache("trade_date", "UNKNOWN_DATE")  # 거래 날짜
    return LOG_DIR / f"{tkr}_{dt}"  # logs/research_dialogs/GOOGL_2025-03-28


# BullNode: Bull 에이전트를 이용한 노드
class BullNode(BaseNode):
    def __init__(self, name: str = "Bull"):  # 노드 이름 초기화
        super().__init__(name)  # BaseNode 초기화
        self.agent = BullResearcher(name=f"{name} Analyst")  # Bull 에이전트 생성

    def run(self, context: Context) -> Context:  # 노드 실행 메서드
        # 1. Bull 에이전트 실행
        context = self.agent.run(context)
        # 2. 노드 상태를 'passed'로 변경
        self.state = 'passed'  # 'pending' → 'running' → 'passed'

        # 3. 토론 로그를 JSON 파일로 저장 (디버깅 및 기록용)
        try:  # 예외 처리
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")  # 타임스탬프 생성
            _write_json(  # JSON 파일 저장
                _round_dir(context) / f"bull_round_{context.get_cache('count',0)}_{ts}.json",  # 파일 경로
                {  # 저장할 데이터
                    "time": datetime.now().isoformat(),  # 타임스탬프
                    "history_tail": context.get_cache("current_response", ""),  # Bull의 마지막 발언
                    "count": context.get_cache("count", 0),  # 현재 토론 카운트
                },
            )
        except Exception as e:  # 로그 저장 실패 시
            print("[BullNode][log]", e)  # 에러 메시지 출력

        return context  # 업데이트된 Context 반환

# BearNode
class BearNode(BaseNode):
    def __init__(self, name: str = "Bear"):  # 노드 이름 초기화
        super().__init__(name)  # BaseNode 초기화
        self.agent = BearResearcher(name=f"{name} Analyst")  # Bear 에이전트 생성
    def run(self, context: Context) -> Context:  # 노드 실행 메서드
        # 1. Bear 에이전트 실행
        context = self.agent.run(context)

        # 2단계: 노드 상태를 'passed'로 변경
        self.state = 'passed'  # 다음 노드로 이동 가능

        # 3단계: 토론 로그를 JSON 파일로 저장
        try:  # 예외 처리
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")  # 타임스탬프 생성
            _write_json(  # JSON 파일 저장
                _round_dir(context) / f"bear_round_{context.get_cache('count',0)}_{ts}.json",  # 파일 경로
                {  # 저장할 데이터
                    "time": datetime.now().isoformat(),  # ISO 타임스탬프
                    "history_tail": context.get_cache("current_response", ""),  # Bear의 마지막 발언
                    "count": context.get_cache("count", 0),  # 현재 토론 카운트
                },
            )
        except Exception as e:  # 로그 저장 실패 시
            print("[BearNode][log]", e)  # 에러 메시지 출력

        return context  # 업데이트된 Context 반환

# ManagerNode
class ManagerNode(BaseNode):
    def __init__(self, name: str = "Manager"):  # 노드 이름 초기화
        super().__init__(name)  # BaseNode 초기화
        self.agent = ResearchManager(name=f"{name} Manager")  # Manager 에이전트 생성

    def run(self, context: Context) -> Context:  # 노드 실행 메서드
        # 1. Manager 에이전트 실행
        context = self.agent.run(context)

        # 2. 노드 상태를 'passed'로 변경
        self.state = 'passed'  # 워크플로우 완료

        # 3. 매니저 결정을 JSON 로그 파일로 저장
        try:  # 예외 처리
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")  # 타임스탬프 생성
            _write_json(  # JSON 파일 저장
                _round_dir(context) / f"manager_decision_{ts}.json",  # 파일 경로
                {  # 저장할 데이터
                    "time": datetime.now().isoformat(),  # 타임스탬프
                    "decision": context.get_cache("manager_decision")  # 매니저 전체 결정
                },
            )
        except Exception as e:  # 로그 저장 실패 시
            print("[ManagerNode][log]", e)  # 에러 메시지 출력

        # 4. 투자 계획을 Context에만 저장 (파일로는 저장하지 않음)
        try:
            plan = context.get_cache("manager_decision") or {}
            ticker = context.get_cache("ticker", "UNKNOWN")
            trade_date = context.get_cache("trade_date", "UNKNOWN_DATE")

            # 마크다운 내용 구성
            md = [
                f"# Investment Plan ({ticker} / {trade_date})",
                "",
                f"**Decision:** {plan.get('decision','')}",
                "",
                "## Rationale",
                plan.get("rationale", ""),
                "",
                "## Plan",
                plan.get("plan", ""),
            ]

            investment_plan_content = "\n".join(md)

            # Context의 reports에 저장 (파일은 생성하지 않음)
            context.set_report(ticker, trade_date, "investment_plan", investment_plan_content)

        except Exception as e:
            print("[ManagerNode][save plan]", e)

        return context  # 업데이트된 Context 반환
