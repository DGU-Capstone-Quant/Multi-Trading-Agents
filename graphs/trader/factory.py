from modules.graph.graph import Graph
from graphs.trader.nodes import RiskCheckerNode, TraderNode, TickerLoopNode


def create_trader_graph() -> Graph:
    """
    Trader Graph 구조:
    [TickerLoopNode] → [RiskCheckerNode] → [TraderNode] → (다음 ticker 있으면 루프)
    """
    ticker_loop_node = TickerLoopNode("ticker_loop_node")
    graph = Graph("trader_graph", start_node=ticker_loop_node)

    ticker_loop = graph.start_node.name
    risk_checker = graph.add_node(RiskCheckerNode("risk_checker_node"))
    trader = graph.add_node(TraderNode("trader_node"))

    # ticker_loop → risk_checker (ticker가 있을 때만)
    graph.add_edge(ticker_loop, risk_checker,
                   cond_func=lambda ctx: ticker_loop_node._current_ticker_index < len(ticker_loop_node._tickers))

    # risk_checker → trader
    graph.add_edge(risk_checker, trader)

    # trader → ticker_loop (다음 ticker가 있으면 루프)
    def advance_and_check(ctx):
        if ticker_loop_node.has_next_ticker():
            ticker_loop_node.advance_ticker()
            return True
        return False

    graph.add_edge(trader, ticker_loop, cond_func=advance_and_check)

    return graph
