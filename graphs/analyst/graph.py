# graphs/analyst/graph.py
from modules.graph import Graph
from modules.context import Context
from .node import SelectionNode, AnalystNode

def check_tickers_left(context: Context) -> bool:
    return len(context.get_cache('tickers', [])) > 0

def create_analyst_graph() -> Graph:
    graph = Graph("analyst_graph", start_node=SelectionNode("selection_node"))

    selection_node = graph.start_node.name
    analyst_node = graph.add_node(AnalystNode("analyst_node"))

    graph.add_edge(selection_node, analyst_node)
    graph.add_edge(analyst_node, selection_node, cond_func=check_tickers_left)

    return graph
