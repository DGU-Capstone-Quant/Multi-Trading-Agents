# modules/graph/graph.py
from .node import *

class Graph:
    def __init__(self, start_node: BaseNode):
        self.start_node = start_node
        self.graph: dict[str, BaseNode] = {start_node.name: start_node}

    def run(self, **kwargs) -> dict:
        current_node = self.start_node

        while True:
            current_node.state = 'in_progress'
            kwargs = current_node.run(**kwargs)
            if current_node.state != 'passed':
                continue

            current_node = current_node.get_next_nodes(**kwargs)
            if current_node:
                continue

            break

        return kwargs

    def add_node(self, node: BaseNode) -> str:
        self.graph[node.name] = node
        return node.name

    def add_edge(self, from_node_name: str, to_node_name: str, cond_func=None):
        from_node = self.graph.get(from_node_name)
        to_node = self.graph.get(to_node_name)

        if not from_node:
            raise ValueError(f"Node '{from_node_name}'가 그래프에 없습니다.")
        if not to_node:
            raise ValueError(f"Node '{to_node_name}'가 그래프에 없습니다.")
        
        edge = Edge(to_node, cond_func)
        from_node.add_edge(edge)
            