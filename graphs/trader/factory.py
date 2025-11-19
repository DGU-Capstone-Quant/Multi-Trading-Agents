from pathlib import Path
from modules.graph.graph import Graph
from graphs.trader.nodes import RiskCheckerNode, TraderNode


def create_trader_graph() -> Graph:
    risk_checker = RiskCheckerNode("RiskChecker")
    trader = TraderNode("Trader")

    g = Graph(risk_checker)
    g.add_node(trader)
    g.add_edge("RiskChecker", "Trader")

    return g
