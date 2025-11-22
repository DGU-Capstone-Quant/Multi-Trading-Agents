from modules.graph.graph import Graph
from graphs.trader.nodes import RiskCheckerNode, TraderNode


def create_trader_graph() -> Graph:
    graph = Graph("trader_graph", start_node=RiskCheckerNode("risk_checker_node"))

    risk_checker = graph.start_node.name
    trader = graph.add_node(TraderNode("trader_node"))

    graph.add_edge(risk_checker, trader)

    return graph
