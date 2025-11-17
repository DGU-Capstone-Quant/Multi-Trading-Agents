from pathlib import Path

from modules.graph.node import BaseNode
from graphs.trader.agents import TraderAgent
from modules.context import Context


class TraderNode(BaseNode):
    def __init__(self, name: str = "Trader"):
        super().__init__(name)
        self.agent = TraderAgent(name=f"{name}")

    def run(self, context: Context) -> Context:
        context = self.agent.run(context)
        self.state = 'passed'

        ticker = context.get_cache("ticker", "UNKNOWN")
        decision = context.get_cache("trader_decision", "")
        recommendation = context.get_cache("trader_recommendation", "")

        print(f"\n[{self.name}] Trading Decision for {ticker}:")
        print(f"Decision: {decision}")
        print(f"Recommendation: {recommendation}")

        return context
