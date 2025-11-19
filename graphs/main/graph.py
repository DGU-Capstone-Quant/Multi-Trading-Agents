# graphs/main/graph.py
from modules.graph import Graph
from graphs.analyst import create_analyst_graph
from graphs.rank import create_rank_graph
from graphs.debate.factory import create_debate_graph


def create_main_graph() -> Graph:

    graph = Graph("main_graph", start_node=create_rank_graph())
    rank_graph = graph.start_node.name
    analyst_graph = graph.add_node(create_analyst_graph())
    debate_graph = graph.add_node(create_debate_graph())
    
    graph.add_edge(rank_graph, analyst_graph)
    graph.add_edge(analyst_graph, debate_graph)

    return graph
