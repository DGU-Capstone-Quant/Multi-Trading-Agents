# graphs/main/node.py
from modules.graph import BaseNode
from modules.context import Context

class GraphBeginNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
    
    def run(self, context: Context) -> Context:
        context.set_default_config()
        self.state = 'passed'
        return context