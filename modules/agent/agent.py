# modules/agents/agent.py
from modules.llm import Client
from modules.context import Context

class Agent:
    def __init__(self):
        self.llm_client = Client()

        self.quick_model = "gemini-2.5-flash"
        self.deep_model = "gemini-2.5-pro"

        self.quick_thinking_budget = 0
        self.deep_thinking_budget = -1

        self.tools = []

    def run(self, context: Context) -> Context:
        response = self.llm_client.generate_content(
            model=self.quick_model,
            contents=[context.get_cache("question", "Hello, How are you?")],
            thinking_budget=self.quick_thinking_budget,
        )

        print(f"Agent's answer: {response.content.get('text')}")
        context.set_cache("answer", response.content.get('text'))
        return context

# Test: python -m modules.agent.agent
if __name__ == "__main__":
    agent = Agent()
    context = Context()
    context.set_cache("question", "What is the capital of France?")
    context = agent.run(context)