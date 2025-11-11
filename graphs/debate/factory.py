# graphs/debate/factory.py

from pathlib import Path
from modules.graph.graph import Graph
from graphs.debate.nodes import BullNode, BearNode, ManagerNode
from modules.context import Context

# 유틸리티 함수들
def _primary_report_path(ticker: str, trade_date: str) -> Path:
    return Path("results") / ticker / trade_date / "market_report.md"

def _fallback_report_path(ticker: str, trade_date: str) -> Path:
    return Path("results") / ticker / trade_date / "reports" / "market_report.md"

def _resolve_report_path(ticker: str, trade_date: str) -> Path:
    p1 = _primary_report_path(ticker, trade_date)  # Primary 경로 시도
    if p1.exists():  # Primary 경로에 파일이 있으면
        return p1  # Primary 경로 반환
    p2 = _fallback_report_path(ticker, trade_date)  # Fallback 경로 시도
    if p2.exists():  # Fallback 경로에 파일이 있으면
        return p2  # Fallback 경로 반환
    raise FileNotFoundError(f"market_report.md를 찾지 못 했습니다.: {p1} or {p2}")

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def create_context(ticker: str, trade_date: str, rounds: int = 1) -> Context:
    """토론용 Context 생성 및 초기화"""
    # 마켓 리포트 파일 읽기
    rp = _resolve_report_path(ticker, trade_date)  # 마켓 리포트 파일 경로 찾기
    reports_dir = rp.parent  # 리포트 디렉토리 경로

    ctx = Context()  # 빈 Context 생성

    # 리포트 데이터 저장 (Context.reports에 저장)
    ctx.set_report("market_report", _read(rp))  # 마켓 리포트 읽어서 저장
    # ctx.set_report("sentiment_report", "(auto) none")  # 감정 분석
    # ctx.set_report("news_report", "(auto) none")  # 뉴스 리포트
    # ctx.set_report("fundamentals_report", "(auto) none")  # 펀더멘털 분석

    # 캐시 데이터 저장
    ctx.set_cache(
        ticker=ticker,  # 티커 심볼
        trade_date=trade_date,  # 거래 날짜
        report_path=str(rp),  # 리포트 파일 경로
        report_dir=str(reports_dir),  # 리포트 디렉토리 경로
        history="",  # 전체 토론 히스토리
        bull_history="",  # Bull 전용 히스토리
        bear_history="",  # Bear 전용 히스토리
        current_response="",  # 가장 최근 발언
        count=0,  # 토론 카운트
        rounds=rounds,  # 토론 라운드 수
        max_rounds=rounds,  # 최대 라운드 수
    )

    return ctx

def create_debate_graph(ctx: Context) -> Graph:
    """토론 그래프 생성"""
    # Context에서 rounds 값 가져오기
    rounds = ctx.get_cache("rounds", 1)

    # 1. 노드 생성
    bull = BullNode("Bull")  # Bull 노드 생성
    bear = BearNode("Bear")  # Bear 노드 생성
    mgr = ManagerNode("Manager")  # Manager 노드 생성

    # 2. 그래프 생성 및 노드 추가
    g = Graph(bull)  # Graph 생성 (시작 노드: Bull)
    g.add_node(bear)  # Bear 노드 추가
    g.add_node(mgr)  # Manager 노드 추가

    # 3. 엣지 추가
    g.add_edge("Bull", "Bear")

    # Bear에서 두 개의 엣지
    def check_round_limit(ctx: Context) -> bool:
        """토론 라운드가 제한에 도달했는지 확인"""
        return ctx.get_cache("count", 0) >= rounds * 2

    g.add_edge("Bear", "Manager", cond_func=check_round_limit)
    g.add_edge("Bear", "Bull")  # 위 조건이 False면 Bull로

    return g
