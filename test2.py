from modules.graph.graph import Graph
from modules.graph.node import BaseNode
from modules.context import Context
from modules.agent.agent import Agent
from modules.llm.client import Client
from pydantic import BaseModel


class ArgumentReply(BaseModel):
    chat: str


class JudgmentDecision(BaseModel):
    analysis: str
    winner: str


class ActionAgent(Agent):
    def __init__(self, name: str = "액션파"):
        super().__init__()
        self.name = name
        self.llm_client = Client()

    def run(self, context: Context) -> Context:
        history = context.get_cache("history", "")
        last_arg = context.get_cache("current_response", "")

        contents = [
            f"당신은 {self.name}입니다. 액션 영화를 옹호하는 토론자입니다.",
            "액션 영화가 더 좋은 이유를 1-2문장으로 주장하세요. 흥미진진함과 스트레스 해소 효과를 강조하세요.",
            f"토론 히스토리: {history}",
            f"상대방의 마지막 주장: {last_arg}",
        ]

        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=contents,
            thinking_budget=self.quick_thinking_budget,
            schema=ArgumentReply,
        )

        chat = resp.content.get("chat", "")
        line = f"{self.name}: {chat}"

        new_history = history + ("\n" if history else "") + line

        context.set_cache(
            history=new_history,
            action_argument=chat,
            current_response=line,
            count=context.get_cache("count", 0) + 1,
        )

        return context


class DramaAgent(Agent):
    def __init__(self, name: str = "드라마파"):
        super().__init__()
        self.name = name
        self.llm_client = Client()

    def run(self, context: Context) -> Context:
        history = context.get_cache("history", "")
        last_arg = context.get_cache("current_response", "")

        contents = [
            f"당신은 {self.name}입니다. 드라마 영화를 옹호하는 토론자입니다.",
            "드라마 영화가 더 좋은 이유를 1-2문장으로 주장하세요. 깊이 있는 스토리와 감정적 몰입을 강조하세요.",
            f"토론 히스토리: {history}",
            f"상대방의 마지막 주장: {last_arg}",
        ]

        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=contents,
            thinking_budget=self.quick_thinking_budget,
            schema=ArgumentReply,
        )

        chat = resp.content.get("chat", "")
        line = f"{self.name}: {chat}"

        new_history = history + ("\n" if history else "") + line

        context.set_cache(
            history=new_history,
            drama_argument=chat,
            current_response=line,
            count=context.get_cache("count", 0) + 1,
        )

        return context


class JudgeAgent(Agent):
    def __init__(self, name: str = "심판"):
        super().__init__()
        self.name = name
        self.llm_client = Client()

    def run(self, context: Context) -> Context:
        history = context.get_cache("history", "")

        prompt = f"""당신은 공정한 심판입니다. 토론 내용을 검토하고 승자를 결정하세요.

토론 내용:
{history}

두 주장을 비교 분석하고 승자를 "액션 영화" 또는 "드라마 영화" 중 하나로 결정하세요.
"""

        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=[prompt],
            thinking_budget=self.quick_thinking_budget,
            schema=JudgmentDecision,
        )

        context.set_cache(
            judge_decision=resp.content,
            current_response=f"{self.name}: {resp.content}",
        )

        return context


class ActionNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.agent = ActionAgent(name)

    def run(self, context: Context):
        round_num = context.get_cache("count", 0) // 2 + 1
        print(f"\n[라운드 {round_num}] [{self.name}]")

        context = self.agent.run(context)
        argument = context.get_cache("action_argument", "")
        print(f"주장: {argument}")

        self.state = 'passed'
        return context


class DramaNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.agent = DramaAgent(name)

    def run(self, context: Context):
        round_num = (context.get_cache("count", 0) + 1) // 2
        print(f"\n[라운드 {round_num}] [{self.name}]")

        context = self.agent.run(context)
        argument = context.get_cache("drama_argument", "")
        print(f"주장: {argument}")

        self.state = 'passed'
        return context


class JudgeNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.agent = JudgeAgent(name)

    def run(self, context: Context):
        history = context.get_cache("history", "")

        print(f"\n[{self.name}] 최종 판단!")
        print("\n--- 토론 내용 검토 ---")
        print(history)
        print("\n--- 심판 의견 ---")

        context = self.agent.run(context)
        decision = context.get_cache("judge_decision", {})

        print(f"분석: {decision.get('analysis', '')}")
        print(f"승자: {decision.get('winner', '')} 승리!")

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
                   cond_func=lambda ctx: ctx.get_cache("count", 0) >= max_rounds * 2)
    graph.add_edge("드라마파", "액션파")

    return graph


if __name__ == "__main__":
    print("=== 영화 추천 토론 시작 ===")
    graph = create_movie_graph(max_rounds=4)
    ctx = Context()
    ctx.set_cache(history="", count=0)
    graph.run(ctx)
    print("\n=== 토론 완료 ===")
