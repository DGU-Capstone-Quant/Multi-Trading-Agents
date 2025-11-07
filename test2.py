from modules.graph.graph import Graph
from modules.graph.node import BaseNode
from modules.context import Context
import random


class ActionNode(BaseNode):
    def run(self, context: Context):
        score = random.randint(60, 100)
        print(f"\n[{self.name}] 액션 영화 추천! (점수: {score})")
        context.set_cache(action_score=score)
        self.state = 'passed'
        return context


class DramaNode(BaseNode):
    def run(self, context: Context):
        score = random.randint(60, 100)
        print(f"\n[{self.name}] 드라마 영화 추천! (점수: {score})")
        context.set_cache(drama_score=score)
        self.state = 'passed'
        return context


class JudgeNode(BaseNode):
    def run(self, context: Context):
        action_score = context.get_cache("action_score", 0)
        drama_score = context.get_cache("drama_score", 0)

        print(f"\n[{self.name}] 최종 판단!")
        print(f"액션파: {action_score}점 vs 드라마파: {drama_score}점")

        if action_score > drama_score:
            winner = "액션 영화"
        elif drama_score > action_score:
            winner = "드라마 영화"
        else:
            winner = "무승부"

        print(f"결과: {winner} 승리!" if winner != "무승부" else "결과: 무승부!")

        self.state = 'passed'
        return context


def create_movie_graph():
    action = ActionNode("액션파")
    drama = DramaNode("드라마파")
    judge = JudgeNode("심판")

    graph = Graph(action)
    graph.add_node(drama)
    graph.add_node(judge)

    graph.add_edge("액션파", "드라마파")
    graph.add_edge("드라마파", "심판")

    ctx = Context()

    return graph, ctx


if __name__ == "__main__":
    print("=== 영화 추천 시작 ===")
    graph, ctx = create_movie_graph()
    graph.run(ctx)
    print("\n=== 완료 ===")
