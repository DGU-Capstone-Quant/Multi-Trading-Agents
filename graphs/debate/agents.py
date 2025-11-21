# graphs/debate/agents.py

from datetime import datetime as dt
from modules.agent import Agent
from modules.llm.client import Client
from pydantic import BaseModel
from modules.context import Context


def _normalize_date(date: str) -> str:
    """date 형식을 YYYYMMDDTHHMM으로 변환"""
    if not date:
        return ""
    # 이미 YYYYMMDDTHHMM 형식이면 그대로 반환
    if "T" in date and "-" not in date:
        return date
    # YYYY-MM-DD 형식이면 변환
    try:
        return dt.strptime(date, "%Y-%m-%d").strftime("%Y%m%dT%H%M")
    except ValueError:
        return date


class BullReply(BaseModel):
    """Bull 에이전트의 응답 스키마 - 매수 주장"""
    chat: str


class BearReply(BaseModel):
    """Bear 에이전트의 응답 스키마 - 매도 주장"""
    chat: str


class ManagerDecision(BaseModel):
    """Manager의 최종 결정 스키마"""
    decision: str
    rationale: str
    plan: str


class BullResearcher(Agent):
    """주식 매수를 옹호하는 Bull 에이전트 (낙관적 관점)"""

    def __init__(self, name: str = "Bull Analyst"):
        super().__init__()
        self.name = name
        self.llm_client = Client()

    def run(self, context: Context) -> Context:
        # Context에서 필요한 데이터 읽기
        history = context.get_cache("history", "")
        last_arg = context.get_cache("current_response", "")
        ticker = context.get_cache("ticker", "")
        raw_date = context.get_config("trade_date", "") or context.get_cache("date", "")
        date = _normalize_date(raw_date)

        # config에서 analysis_tasks 가져오기 (기본값: financial, news, fundamental)
        analysis_tasks = context.get_config("analysis_tasks", ["financial", "news", "fundamental"])

        # analyst가 생성한 보고서들을 context.reports에서 가져오기
        reports_text = ""
        for task in analysis_tasks:
            report = context.reports.get(ticker, {}).get(
                dt.strptime(date, "%Y%m%dT%H%M").strftime("%Y%m%dT%H") if date else "", {}
            ).get(task, None)

            if report:
                # analyst의 구조화된 리포트 형식 사용
                if isinstance(report, dict):
                    report_str = context.get_report(ticker, date, task)
                    reports_text += f"=== {task.upper()} ANALYSIS ===\n{report_str}\n\n"
                # 단순 문자열 리포트인 경우 (하위 호환성)
                else:
                    reports_text += f"=== {task.upper()} ANALYSIS ===\n{report}\n\n"

        # 보고서가 없는 경우 경고
        if not reports_text:
            reports_text = "[WARNING] No analyst reports available. Please run analyst graph first.\n\n"

        # 프롬프트 구성
        prompt = f"""You are a Bull Analyst. Use the following analyst reports to support your investment thesis:

{reports_text}
=== DEBATE HISTORY ===
{history}

=== LAST OPPONENT ARGUMENT ===
{last_arg}

Based on the analyst reports above, provide a strong bullish argument with specific evidence from the reports.
"""

        # AI 호출
        contents = [
            f"You are {self.name}, advocating for buying the stock.",
            "Use specific data and insights from the analyst reports to make your case.",
            prompt,
            "Return JSON with field: chat (your argument with evidence).",
        ]

        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=contents,
            thinking_budget=self.quick_thinking_budget,
            schema=BullReply,
        )

        # 응답 파싱 및 저장
        chat = resp.content.get("chat", "")
        line = f"{self.name}: {chat}"

        # 히스토리 업데이트
        new_history = history + ("\n" if history else "") + line
        bull_hist = context.get_cache("bull_history", "")
        new_bull_history = bull_hist + ("\n" if bull_hist else "") + line

        # Context에 결과 저장
        context.set_cache(
            history=new_history,
            bull_history=new_bull_history,
            current_response=line,
            count=context.get_cache("count", 0) + 1,
        )

        return context

class BearResearcher(Agent):
    """주식 매도를 옹호하는 Bear 에이전트 (비관적 관점)"""

    def __init__(self, name: str = "Bear Analyst"):
        super().__init__()
        self.name = name
        self.llm_client = Client()

    def run(self, context: Context) -> Context:
        # Context에서 필요한 데이터 읽기
        history = context.get_cache("history", "")
        last_arg = context.get_cache("current_response", "")
        ticker = context.get_cache("ticker", "")
        raw_date = context.get_config("trade_date", "") or context.get_cache("date", "")
        date = _normalize_date(raw_date)

        # config에서 analysis_tasks 가져오기 (기본값: financial, news, fundamental)
        analysis_tasks = context.get_config("analysis_tasks", ["financial", "news", "fundamental"])

        # analyst가 생성한 보고서들을 context.reports에서 가져오기
        reports_text = ""
        for task in analysis_tasks:
            report = context.reports.get(ticker, {}).get(
                dt.strptime(date, "%Y%m%dT%H%M").strftime("%Y%m%dT%H") if date else "", {}
            ).get(task, None)

            if report:
                # analyst의 구조화된 리포트 형식 사용
                if isinstance(report, dict):
                    report_str = context.get_report(ticker, date, task)
                    reports_text += f"=== {task.upper()} ANALYSIS ===\n{report_str}\n\n"
                # 단순 문자열 리포트인 경우 (하위 호환성)
                else:
                    reports_text += f"=== {task.upper()} ANALYSIS ===\n{report}\n\n"

        # 보고서가 없는 경우 경고
        if not reports_text:
            reports_text = "[WARNING] No analyst reports available. Please run analyst graph first.\n\n"

        # 프롬프트 구성
        prompt = f"""You are a Bear Analyst. Use the following analyst reports to identify risks and concerns:

{reports_text}
=== DEBATE HISTORY ===
{history}

=== LAST OPPONENT ARGUMENT ===
{last_arg}

Based on the analyst reports above, provide a strong bearish argument highlighting risks and concerns with specific evidence from the reports.
"""

        # AI 호출
        contents = [
            f"You are {self.name}, advocating caution and highlighting risks.",
            "Use specific data and insights from the analyst reports to identify concerns.",
            prompt,
            "Return JSON with field: chat (your argument with evidence).",
        ]

        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=contents,
            thinking_budget=self.quick_thinking_budget,
            schema=BearReply,
        )

        # 응답 파싱 및 저장
        chat = resp.content.get("chat", "")
        line = f"{self.name}: {chat}"

        # 히스토리 업데이트
        new_history = history + ("\n" if history else "") + line
        bear_hist = context.get_cache("bear_history", "")
        new_bear_history = bear_hist + ("\n" if bear_hist else "") + line

        # Context에 결과 저장
        context.set_cache(
            history=new_history,
            bear_history=new_bear_history,
            current_response=line,
            count=context.get_cache("count", 0) + 1,
        )

        return context


class ResearchManager(Agent):
    """토론을 종합하여 최종 투자 결정을 내리는 Manager 에이전트"""

    def __init__(self, name: str = "Research Manager"):
        super().__init__()
        self.name = name
        self.llm_client = Client()

    def run(self, context: Context) -> Context:
        # Context에서 전체 토론 히스토리 읽기
        history = context.get_cache("history", "")

        # 프롬프트 구성
        prompt = f"""As the portfolio manager ({self.name}), read the debate below and output a clear decision.

Debate:
{history}

Return JSON with:
- decision: "BUY"|"SELL"|"HOLD"
- rationale: concise reasoning
- plan: concrete next steps
"""

        # AI 호출
        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=[prompt],
            thinking_budget=self.quick_thinking_budget,
            schema=ManagerDecision,
        )

        # Context에 결과 저장
        context.set_cache(
            manager_decision=resp.content,
            current_response=f"{self.name}: {resp.content}",
        )

        return context