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
        trade_date = context.get_cache("trade_date", "UNKNOWN_DATE")
        report_dir = context.get_cache("report_dir", "results")
        reports_dir = Path(report_dir)

        decision = context.get_cache("trader_decision", "")
        recommendation = context.get_cache("trader_recommendation", "")

        md = [
            f"# Trading Decision for {ticker}",
            f"**Date**: {trade_date}",
            "",
            "## Final Decision",
            f"**{decision}**",
            "",
            "## Recommendation",
            recommendation,
        ]

        trader_decision_content = "\n".join(md)
        (reports_dir / "trader_decision.md").write_text(trader_decision_content, encoding="utf-8")
        context.set_report("trader_decision", trader_decision_content)

        print(f"\n[{self.name}] Trading Decision:")
        print(f"Decision: {decision}")
        print(f"Recommendation: {recommendation}")

        return context
