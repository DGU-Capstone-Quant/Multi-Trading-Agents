# modules/graph/node.py
from modules.context import Context


class Edge:  # 노드 간의 방향성 있는 연결을 나타내는 클래스
    def __init__(self, to_node: 'BaseNode', cond_func=None):  # Edge 초기화
        self.to_node = to_node  # 이 엣지가 가리키는 목적지 노드 저장
        self.cond_func = cond_func  # 조건 함수 저장

    def is_condition_met(self, context: Context) -> bool:  # 이 엣지의 조건이 만족되는지 검사
        if self.cond_func is None:  # 조건 함수가 없으면
            return True  # 항상 True 반환
        return self.cond_func(context)  # 조건 함수가 있으면 함수 실행 결과 반환

class BaseNode:  # 워크플로우의 실행 단위를 나타내는 추상 베이스 클래스
    def __init__(self, name: str):  # BaseNode 초기화: name을 받아 초기 상태 설정
        self.name = name  # 노드의 고유 이름 저장
        self.state = 'pending'  # 노드의 실행 상태 초기화 pending,running,passed
        self.edges: list[Edge] = []  # 이 노드에서 나가는 엣지들의 리스트

    def run(self, context: Context):  # 노드의 실제 작업을 수행하는 메서드
        raise NotImplementedError("BaseNode의 run 메서드는 서브클래스에서 구현되어야 함")

    def get_next_nodes(self, context: Context):  # 현재 노드 다음에 실행할 노드를 결정하는 메서드
        for edge in self.edges:  # 이 노드의 모든 엣지를 순서대로 순회
            if edge.is_condition_met(context):  # 현재 엣지의 조건이 만족되는지 검사
                return edge.to_node  # 조건을 만족하는 첫 번째 엣지의 목적지 노드 반환
        return None  # 모든 엣지의 조건이 False면 None 반환

    def add_edge(self, edge: Edge):  # 이 노드에 새로운 엣지를 추가하는 메서드
        self.edges.append(edge)  # 엣지를 edges 리스트 끝에 추가