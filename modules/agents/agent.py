# modules/agents/agent.py
from modules.llm import Client

class Agent:
    def __init__(self):
        self.llm_client = Client()

    def ask(self, question: str) -> str:
        response, _, _ = self.llm_client.generate_content(
            model="gemini-2.5-flash",
            contents=[question]
        )
        return response

# Test: python -m modules.agents.agent
if __name__ == "__main__":
    agent = Agent()
    answer = agent.ask("What is the capital of France?")
    print(f"Agent's answer: {answer}")