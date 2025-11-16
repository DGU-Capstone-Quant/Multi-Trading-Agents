# graphs/analyst/node.py
from modules.graph import BaseNode
from modules.context import Context
from .agent import AnalystAgent


class AnalystNode(BaseNode):
    def __init__(self, name: str, task: str):
        super().__init__(name)
        self.task = task
        self.agent: AnalystAgent = AnalystAgent(task=task)

    def run(self, context: Context) -> Context:
        self.agent.run(context)
        if context.get_report(self.task):
            self.state = 'passed'
        return context