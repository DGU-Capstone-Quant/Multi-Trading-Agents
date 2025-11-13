# graphs/analyst/agent.py
from modules.agent import Agent
from modules.context import Context

class AnalystAgent(Agent):
    def __init__(self, name: str):
        super().__init__()
        self.name = name