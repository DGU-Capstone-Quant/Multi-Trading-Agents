# graphs/debate/factory.py

from modules.graph.graph import Graph
from graphs.debate.nodes import BullNode, BearNode, ManagerNode, DebateSelectionNode
from modules.context import Context


def check_tickers_left(context: Context) -> bool:
    """남은 ticker가 있는지 확인"""
    return len(context.get_cache('tickers', [])) > 0


def check_round_limit(context: Context) -> bool:
    """토론 라운드가 제한에 도달했는지 확인"""
    rounds = context.get_config("rounds", 1)
    return context.get_cache("count", 0) >= rounds * 2


def create_debate_graph() -> Graph:
    """
    토론 그래프 생성 - analyst 패턴을 따름
    SelectionNode -> Bull -> Bear -> (라운드 체크) -> Manager -> (ticker 체크) -> SelectionNode
    """
    # 시작 노드: DebateSelectionNode
    graph = Graph("debate_graph", start_node=DebateSelectionNode("selection_node"))

    selection_node = graph.start_node.name

    # 토론 노드들 추가
    bull_node = graph.add_node(BullNode("bull_node"))
    bear_node = graph.add_node(BearNode("bear_node"))
    manager_node = graph.add_node(ManagerNode("manager_node"))

    # 엣지 연결
    # selection -> bull (ticker 선택 후 토론 시작)
    graph.add_edge(selection_node, bull_node)

    # bull -> bear (Bull 발언 후 Bear 차례)
    graph.add_edge(bull_node, bear_node)

    # bear -> manager (라운드 제한 도달 시)
    graph.add_edge(bear_node, manager_node, cond_func=check_round_limit)

    # bear -> bull (라운드 제한 미도달 시 토론 계속)
    graph.add_edge(bear_node, bull_node)

    # manager -> selection (다음 ticker 처리를 위해, ticker가 남아있으면)
    graph.add_edge(manager_node, selection_node, cond_func=check_tickers_left)

    return graph