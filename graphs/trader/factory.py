from pathlib import Path
from modules.graph.graph import Graph
from graphs.trader.nodes import TraderNode


def create_trader_graph() -> Graph:
    trader = TraderNode("Trader")
    g = Graph(trader)
    return g
