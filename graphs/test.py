# graphs/test.py
from modules.graph.graph import Graph
from modules.graph.node import BaseNode
from modules.agent import Agent
from pydantic import BaseModel


class TestSchema(BaseModel):
    name: str
    chat: str

class TestAgent(Agent):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def run(self, **kwargs):
        response = self.llm_client.generate_content(
            model=self.quick_model,
            contents=[
                f"주제: {kwargs.get('subject', '없음')}",
                kwargs.get("chat_history", ""),
                f"앞선 대화 내용을 바탕으로 다음 대화를 이어가세요. 당신의 name은 {self.name}입니다."
                ],
            thinking_budget=self.quick_thinking_budget,
            schema=TestSchema,
        )

        chat = response.content.get("chat")
        line = f"{self.name}: {chat}"
        print(f"{line}\n")

        kwargs["chat_history"] = kwargs.get("chat_history", "") + f"\n{line}"

        return kwargs

class TestNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.agent = TestAgent(name)

    def run(self, **kwargs):
        kwargs = self.agent.run(**kwargs)
        self.state = 'passed'
        kwargs["chat_count"] = kwargs.get("chat_count", 0) + 1
        return kwargs


def check_chat_times(**kwargs) -> bool:
    chat_count = kwargs.get("chat_count", 0)
    return chat_count < kwargs.get("max_chats", 5) * 2

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
    test_graph = create_test_graph()
    test_graph.run()