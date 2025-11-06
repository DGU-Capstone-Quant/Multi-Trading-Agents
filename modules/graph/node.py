# modules/graph/node.py
from modules.context import Context


class Edge:
    def __init__(self, to_node: 'BaseNode', cond_func=None):
        self.to_node = to_node
        self.cond_func = cond_func

    def is_condition_met(self, context: Context) -> bool:
        if self.cond_func is None:
            return True
        return self.cond_func(context)

class BaseNode:
    def __init__(self, name: str):
        self.name = name
        self.state = 'pending' # 가능한 상태: 'pending', 'running', 'passed'
        self.edges: list[Edge] = []

    def run(self, context: Context):
        raise NotImplementedError("BaseNode의 run 메서드는 서브클래스에서 구현되어야 함")
    
    def get_next_nodes(self, context: Context):
        for edge in self.edges:
            if edge.is_condition_met(context):
                return edge.to_node
        return None
    
    def add_edge(self, edge: Edge):
        self.edges.append(edge)