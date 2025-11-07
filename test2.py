from modules.graph.graph import Graph
from modules.graph.node import BaseNode
from modules.context import Context
from modules.agent.agent import Agent


class ActionNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.agent = Agent()

    def run(self, context: Context):
        round_num = context.get_cache("round", 0) + 1
        drama_arg = context.get_cache("drama_argument", "")

        prompt = f"당신은 액션 영화를 추천하는 토론자입니다. "
        if drama_arg:
            prompt += f"상대방의 주장: '{drama_arg}'. 이에 대해 반박하면서 "
        prompt += "액션 영화가 더 좋은 이유를 1-2문장으로 주장하세요. 박진감, 스트레스 해소 등을 강조하세요."

        context.set_cache(question=prompt)
        context = self.agent.run(context)
        argument = context.get_cache("answer", "")

        print(f"\n[라운드 {round_num}] [{self.name}]")
        print(f"주장: {argument}")
        context.set_cache(action_argument=argument, round=round_num)
        self.state = 'passed'
        return context


class DramaNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.agent = Agent()

    def run(self, context: Context):
        round_num = context.get_cache("round", 0)
        action_arg = context.get_cache("action_argument", "")

        prompt = f"당신은 드라마 영화를 추천하는 토론자입니다. "
        if action_arg:
            prompt += f"상대방의 주장: '{action_arg}'. 이에 대해 반박하면서 "
        prompt += "드라마 영화가 더 좋은 이유를 1-2문장으로 주장하세요. 깊이, 감동, 스토리텔링 등을 강조하세요."

        context.set_cache(question=prompt)
        context = self.agent.run(context)
        argument = context.get_cache("answer", "")

        print(f"\n[라운드 {round_num}] [{self.name}]")
        print(f"주장: {argument}")
        context.set_cache(drama_argument=argument)
        self.state = 'passed'
        return context


class JudgeNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.agent = Agent()

    def run(self, context: Context):
        action_arg = context.get_cache("action_argument", "")
        drama_arg = context.get_cache("drama_argument", "")

        print(f"\n[{self.name}] 최종 판단!")
        print("\n--- 토론 내용 검토 ---")
        print(f"액션파: {action_arg}")
        print(f"드라마파: {drama_arg}")

        print("\n--- 심판 의견 ---")

        prompt = f"""당신은 공정한 심판입니다. 두 토론자의 주장을 듣고 승자를 결정하세요.

액션파 주장: {action_arg}
드라마파 주장: {drama_arg}

두 주장을 비교 분석하고, 어느 쪽이 더 설득력 있었는지 판단한 뒤,
"액션 영화 승리!" 또는 "드라마 영화 승리!"로 끝나는 2-3문장의 판결문을 작성하세요."""

        context.set_cache(question=prompt)
        context = self.agent.run(context)
        judgment = context.get_cache("answer", "")

        print(judgment)

        self.state = 'passed'
        return context


def create_movie_graph(max_rounds=2):
    action = ActionNode("액션파")
    drama = DramaNode("드라마파")
    judge = JudgeNode("심판")

    graph = Graph(action)
    graph.add_node(drama)
    graph.add_node(judge)

    graph.add_edge("액션파", "드라마파")
    graph.add_edge("드라마파", "심판",
                   cond_func=lambda ctx: ctx.get_cache("round", 0) >= max_rounds)
    graph.add_edge("드라마파", "액션파")

    return graph


if __name__ == "__main__":
    print("=== 영화 추천 시작 ===")
    graph = create_movie_graph(max_rounds=2)
    ctx = Context()
    graph.run(ctx)
    print("\n=== 완료 ===")
