# graphs/main/graph.py
from modules.graph import Graph
from graphs.analyst import create_analyst_graph
from graphs.rank import create_rank_graph
from graphs.debate.factory import create_debate_graph
from .node import GraphBeginNode


def create_main_graph() -> Graph:

    graph = Graph("main_graph", start_node=GraphBeginNode("graph_begin"))
    rank_graph = graph.add_node(create_rank_graph())
    analyst_graph = graph.add_node(create_analyst_graph())
    debate_graph = graph.add_node(create_debate_graph())
    
    graph.add_edge("graph_begin", rank_graph)
    graph.add_edge(rank_graph, analyst_graph)
    graph.add_edge(analyst_graph, debate_graph)

    return graph
