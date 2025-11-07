# graphs/debate/agents.py

from modules.agent import Agent  # 베이스 에이전트 클래스
from modules.llm.client import Client
from pydantic import BaseModel
from modules.context import Context

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


COMMON_CONTEXT_TMPL = """[MARKET REPORT]
{market_report}

[SENTIMENT]
{sentiment_report}

[NEWS]
{news_report}

[FUNDAMENTALS]
{fundamentals_report}

[DEBATE HISTORY]
{history}

[LAST OPPONENT ARG]
{last_arg}
"""

# BullResearcher
class BullResearcher(Agent):
    """주식 매수를 옹호하는 Bull 에이전트 (낙관적 관점)"""

    def __init__(self, name: str = "Bull Analyst"):  # 에이전트 이름 초기화
        super().__init__()  # 부모 Agent 클래스 초기화
        self.name = name  # 에이전트 이름 저장
        self.llm_client = Client()  # 클라이언트 생성

    def run(self, context: Context) -> Context:  # 에이전트 실행 메서드
        # Context에서 필요한 데이터 읽기
        history = context.get_cache("history", "")  # 전체 토론 히스토리
        last_arg = context.get_cache("current_response", "")  # 상대방의 마지막 주장
        # AI에게 전달할 프롬프트 구성
        prompt = COMMON_CONTEXT_TMPL.format(  # 공통 템플릿에 데이터 삽입
            market_report=context.get_report("market_report"),  # 시장 리포트
            sentiment_report=context.get_report("sentiment_report"),  # 감정 분석
            news_report=context.get_report("news_report"),  # 뉴스 정보
            fundamentals_report=context.get_report("fundamentals_report"),  # 펀더멘털 분석
            history=history,  # 토론 히스토리
            last_arg=last_arg,  # 상대방의 마지막 주장
        )

        # 메시지 리스트 구성
        contents = [
            f"You are {self.name}, a Bull Analyst advocating for investing in the stock.",
            "Debate concisely with strong evidence.",
            prompt,
            "Return JSON with field: chat (your argument).",
        ]

        # AI 호출
        resp = self.llm_client.generate_content(  # 콘텐츠 생성 요청
            model=self.quick_model,  # gemini-2.5-flash
            contents=contents,  # 위에서 만든 메시지 리스트
            thinking_budget=self.quick_thinking_budget,  # 사고 시간
            schema=BullReply,  # 구조화된 출력 스키마
        )

        # 응답 파싱 및 저장
        chat = resp.content.get("chat", "")  # 주장 텍스트 추출
        line = f"{self.name}: {chat}"  # 포매팅

        # 전체 토론 히스토리 업데이트
        new_history = history + ("\n" if history else "") + line  # 기존 히스토리에 새 발언 추가

        # Bull 히스토리 업데이트
        bull_hist = context.get_cache("bull_history", "")  # 기존 Bull 히스토리
        new_bull_history = bull_hist + ("\n" if bull_hist else "") + line  # Bull 히스토리에 추가

        # 5단계: Context에 결과 저장
        context.set_cache(  # 여러 값을 한번에 저장
            history=new_history,  # 전체 토론 히스토리 업데이트
            bull_history=new_bull_history,  # Bull 전용 히스토리 업데이트
            current_response=line,  # 가장 최근 발언 저장
            count=context.get_cache("count", 0) + 1,  # 토론 카운트 증가
        )

        return context  # 업데이트된 Context 반환

# BearResearcher
class BearResearcher(Agent):
    def __init__(self, name: str = "Bear Analyst"):  # 에이전트 이름 초기화
        super().__init__()  # 부모 Agent 클래스 초기화
        self.name = name  # 에이전트 이름 저장
        self.llm_client = Client()  # 클라이언트 생성

    def run(self, context: Context) -> Context:  # 에이전트 실행 메서드
        # Context에서 필요한 데이터 읽기
        history = context.get_cache("history", "")  # 전체 토론 히스토리
        last_arg = context.get_cache("current_response", "")  # 상대방의 마지막 주장

        # AI에게 전달할 프롬프트 구성
        prompt = COMMON_CONTEXT_TMPL.format(  # 공통 템플릿에 데이터 삽입
            market_report=context.get_report("market_report"),  # 시장 리포트
            sentiment_report=context.get_report("sentiment_report"),  # 감정 분석
            news_report=context.get_report("news_report"),  # 뉴스 정보
            fundamentals_report=context.get_report("fundamentals_report"),  # 펀더멘털 분석
            history=history,  # 토론 히스토리
            last_arg=last_arg,  # 상대방의 마지막 주장
        )

        # AI에게 전달할 메시지 리스트 구성
        contents = [
            f"You are {self.name}, a Bear Analyst emphasizing risks and downsides.",
            "Debate concisely with strong evidence.",
            prompt, 
            "Return JSON with field: chat (your argument).",
        ]

        # AI 호출
        resp = self.llm_client.generate_content(  # 콘텐츠 생성 요청
            model=self.quick_model,  # gemini-2.5-flash
            contents=contents,  # 메시지 리스트
            thinking_budget=self.quick_thinking_budget,  # 사고 시간
            schema=BearReply,  # 구조화된 출력 스키마
        )

        # 4단계: AI 응답 파싱 및 저장
        chat = resp.content.get("chat", "")  # 텍스트 추출
        line = f"{self.name}: {chat}"  # 포매팅

        # 전체 토론 히스토리 업데이트
        new_history = history + ("\n" if history else "") + line  # 히스토리에 새 발언 추가

        # Bear 히스토리 업데이트
        bear_hist = context.get_cache("bear_history", "")  # 기존 Bear 히스토리
        new_bear_history = bear_hist + ("\n" if bear_hist else "") + line  # Bear 히스토리에 추가

        # 5단계: Context에 결과 저장
        context.set_cache(  # 여러 값을 한번에 저장
            history=new_history,  # 전체 토론 히스토리 업데이트
            bear_history=new_bear_history,  # Bear 전용 히스토리 업데이트
            current_response=line,  # 가장 최근 발언 저장 (다음 Bull이 읽을 내용)
            count=context.get_cache("count", 0) + 1,  # 토론 카운트 증가 (종료 조건 체크용)
        )

        return context  # 업데이트된 Context 반환


# ResearchManager
class ResearchManager(Agent):
    def __init__(self, name: str = "Research Manager"):  # 매니저 이름 초기화
        super().__init__()  # 클래스 초기화
        self.name = name  # 매니저 이름 저장
        self.llm_client = Client()  # 클라이언트 생성

    def run(self, context: Context) -> Context:  # 매니저 실행 메서드
        # Context에서 전체 토론 히스토리 읽기
        history = context.get_cache("history", "")  # Bull과 Bear의 전체 토론 내용

        # AI에게 전달할 프롬프트 구성
        prompt = f"""As the portfolio manager ({self.name}), read the debate below and output a clear decision.

Debate:
{history}

Return JSON with:
- decision: "BUY"|"SELL"|"HOLD"
- rationale: concise reasoning
- plan: concrete next steps
"""  # 매니저의 역할과 출력 형식을 명확히 지시

        # AI 호출
        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=[prompt],  # 프롬프트 전달
            thinking_budget=self.quick_thinking_budget,  # 사고 시간
            schema=ManagerDecision,  # 구조화된 출력 스키마
        )

        # AI 응답을 Context에 저장
        context.set_cache(  # 매니저의 결정을 저장
            manager_decision=resp.content,  # 전체 결정 내용
            current_response=f"{self.name}: {resp.content}",  # 매니저의 응답을 문자열로 저장
        )

        return context
