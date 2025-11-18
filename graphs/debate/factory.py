# graphs/debate/factory.py

from modules.graph.graph import Graph
from graphs.debate.nodes import BullNode, BearNode, ManagerNode
from modules.context import Context


def run_debate(context: Context) -> Context:
    """
    여러 ticker에 대해 순차적으로 토론을 실행하고 결과를 context에 저장
    """
    # config에서 설정 값 가져오기
    tickers = context.get_config("tickers", [])

    # 각 ticker에 대해 순차적으로 토론 진행
    for ticker in tickers:
        # 토론에 필요한 캐시 데이터 초기화
        context.set_cache(
            ticker=ticker,
            history="",  # 전체 토론 히스토리
            bull_history="",  # Bull 전용 히스토리
            bear_history="",  # Bear 전용 히스토리
            current_response="",  # 가장 최근 발언
            count=0,  # 토론 카운트
        )

        # 토론 그래프 생성 및 실행
        graph = _create_graph()
        context = graph.run(context)

    return context


def _create_graph() -> Graph:
    """
    토론 그래프 생성
    """
    # 노드 생성
    bull = BullNode("Bull")
    bear = BearNode("Bear")
    mgr = ManagerNode("Manager")

    # 그래프 생성 및 노드 추가
    g = Graph("DebateGraph", bull)
    g.add_node(bear)
    g.add_node(mgr)

    # 엣지 추가
    g.add_edge("Bull", "Bear")

    # 라운드 제한 확인 함수
    def check_round_limit(ctx: Context) -> bool:
        """토론 라운드가 제한에 도달했는지 확인"""
        rounds = ctx.get_config("rounds", 1)
        return ctx.get_cache("count", 0) >= rounds * 2

    # Bear에서 Manager로 가는 조건부 엣지
    g.add_edge("Bear", "Manager", cond_func=check_round_limit)
    # Bear에서 Bull로 돌아가는 엣지
    g.add_edge("Bear", "Bull")

    return g