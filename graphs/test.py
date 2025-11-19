# graphs/test.py
from modules.context import Context
from modules.graph import Graph
from modules.graph import BaseNode
from modules.agent import Agent
from pydantic import BaseModel


class TestSchema(BaseModel):
    name: str
    chat: str

class TestAgent(Agent):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def run(self, context: Context) -> Context:
        contents = [
            f"주제: {context.get_cache('subject', '없음')}",
            context.get_cache("chat_history", ""),
            f"앞선 대화 내용을 바탕으로 다음 대화를 이어가세요. 당신의 name은 {self.name}입니다."
        ]
        response = self.llm_client.generate_content(
            model=self.quick_model,
            contents=contents,
            thinking_budget=self.quick_thinking_budget,
            schema=TestSchema,
        )

        chat = response.content.get("chat")
        line = f"{self.name}: {chat}"
        print(f"{line}\n")

        context.set_cache(chat_history=context.get_cache("chat_history", "") + f"\n{line}")

        return context

class TestNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.agent = TestAgent(name)

    def run(self, context: Context):
        context = self.agent.run(context)
        self.state = 'passed'
        context.set_cache(chat_count=context.get_cache("chat_count", 0) + 1)
        
        return context


def check_chat_times(context: Context) -> bool:
    return context.get_cache("chat_count", 0) < context.get_cache("max_chats", 5) * 2

def create_test_graph() -> Graph:
    start_node = TestNode("Agent A")
    second_node = TestNode("Agent B")

    graph = Graph(start_node)
    graph.add_node(second_node)
    graph.add_edge("Agent A", "Agent B")
    graph.add_edge("Agent B", "Agent A", cond_func=check_chat_times)

    return graph



# Test: python -m graphs.test
if __name__ == "__main__":
    context = Context()
    test_graph = create_test_graph()
    test_graph.run(context)