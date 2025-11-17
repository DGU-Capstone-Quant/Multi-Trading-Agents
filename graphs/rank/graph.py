# graphs/analyst/graph.py
from modules.graph import Graph
from modules.context import Context
from .node import CandidateNode, CheckNode, RankNode
from graphs.analyst import create_analyst_graph


def check_report_making_condition(context: Context) -> bool:
    return len(context.get_cache('no_report_candidates', [])) > 0
    

def create_rank_graph() -> Graph:
    rank_graph = Graph("rank_graph", start_node=CandidateNode("candidate_node"))

    candidate_node = rank_graph.start_node.name
    check_node = rank_graph.add_node(CheckNode("check_node"))
    analyst_graph = rank_graph.add_node(create_analyst_graph())
    rank_node = rank_graph.add_node(RankNode("rank_node"))

    rank_graph.add_edge(candidate_node, check_node)
    rank_graph.add_edge(check_node, analyst_graph, cond_func=check_report_making_condition)
    rank_graph.add_edge(check_node, rank_node)
    rank_graph.add_edge(analyst_graph, rank_node)

    return rank_graph
    
    