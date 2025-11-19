# graphs/main/graph.py
from modules.graph import Graph
from modules.context import Context
from graphs.analyst import create_analyst_graph
from graphs.rank import create_rank_graph
from graphs.debate.factory import create_debate_graph


def create_main_graph() -> Graph:
    rank_graph = create_rank_graph()
    analyst_graph = create_analyst_graph()
    debate_graph = create_debate_graph()

    graph = Graph("main_graph", start_node=rank_graph)
    graph.add_edge(rank_graph, analyst_graph)
    graph.add_edge(analyst_graph, debate_graph)

    return graph
