# modules/agents/agent.py
from modules.llm import Client

class Agent:
    def __init__(self):
        self.llm_client = Client()

        self.quick_model = "gemini-2.5-flash"
        self.deep_model = "gemini-2.5-pro"

        self.quick_thinking_budget = 0
        self.deep_thinking_budget = -1

        self.tools = []

    def run(self, **kwargs):
        response = self.llm_client.generate_content(
            model=self.quick_model,
            contents=[kwargs.get("question", "Hello, world!")],
            thinking_budget=self.quick_thinking_budget,
        )

        print(f"Agent's answer: {response.content.get('text')}")


if __name__ == "__main__":
    agent = Agent()
    answer = agent.run(question="What is the capital of France?")