# modules/graph/node.py


class Edge:
    def __init__(self, to_node: 'BaseNode', cond_func=None):
        self.to_node = to_node
        self.cond_func = cond_func

    def is_condition_met(self, **kwargs) -> bool:
        if self.cond_func is None:
            return True
        return self.cond_func(**kwargs)

class BaseNode:
    def __init__(self, name: str):
        self.name = name
        self.state = 'pending' # 가능한 상태: 'pending', 'running', 'passed'
        self.edges: list[Edge] = []

    def run(self, **kwargs):
        raise NotImplementedError("BaseNode의 run 메서드는 서브클래스에서 구현되어야 함")
    
    def get_next_nodes(self, **kwargs):
        for edge in self.edges:
            if edge.is_condition_met(**kwargs):
                return edge.to_node
        return None
    
    def add_edge(self, edge: Edge):
        self.edges.append(edge)