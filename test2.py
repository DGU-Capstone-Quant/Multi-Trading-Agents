from modules.graph.graph import Graph
from modules.graph.node import BaseNode
from modules.context import Context
import random


class ActionNode(BaseNode):
    def run(self, context: Context):
        argument = "박진감 넘치는 장면과 스릴넘치는 연출로 과제로 받은 스트레스를 날려줍니다."
        print(f"\n[{self.name}]")
        print(f"주장: {argument}")
        context.set_cache(action_argument=argument)
        self.state = 'passed'
        return context


class DramaNode(BaseNode):
    def run(self, context: Context):
        argument = "드라마는 깊이 있는 스토리와 감동적인 연기로 관객의 마음을 움직입니다. 인간의 감정과 삶을 진지하게 다루어 오랫동안 기억에 남습니다."
        print(f"\n[{self.name}]")
        print(f"주장: {argument}")
        context.set_cache(drama_argument=argument)
        self.state = 'passed'
        return context


class JudgeNode(BaseNode):
    def run(self, context: Context):
        action_arg = context.get_cache("action_argument", "")
        drama_arg = context.get_cache("drama_argument", "")

        print(f"\n[{self.name}] 최종 판단!")
        print("\n--- 토론 내용 검토 ---")
        print(f"액션파: {action_arg}")
        print(f"드라마파: {drama_arg}")

        print("\n--- 심판 의견 ---")

        winner = random.choice(["액션", "드라마"])

        if winner == "액션":
            judgment = "두 장르 모두 각자의 매력이 있지만, 오늘은 액션의 스트레스 해소 효과가 더 설득력 있었습니다."
            result = "액션 영화 승리!"
        else:
            judgment = "두 장르 모두 각자의 매력이 있지만, 오늘은 드라마의 깊이 있는 스토리텔링이 더 설득력 있었습니다."
            result = "드라마 영화 승리!"

        print(judgment)
        print(f"\n결과: {result}")

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

    return graph


if __name__ == "__main__":
    print("=== 영화 추천 시작 ===")
    graph = create_movie_graph()
    ctx = Context()
    graph.run(ctx)
    print("\n=== 완료 ===")
