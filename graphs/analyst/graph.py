# graphs/analyst/graph.py
from modules.graph import Graph
from modules.context import Context
from .node import AnalystNode

# 아직 병렬 처리는 지원하지 않음
def create_analyst_graph(context: Context) -> Graph:
    tasks = context.get_config("analysis_tasks", [])
    nodes = [AnalystNode(name=f"AnalystNode_{task}", task=task) for task in tasks]
    graph = Graph(start_node=nodes[0])
    p = nodes[0].name
    for i in range(len(nodes) - 1):
        n = graph.add_node(nodes[i])
        graph.add_edge(p, n)
        p = n
    return graph
