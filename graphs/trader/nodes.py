from pathlib import Path
from datetime import datetime
import json

from modules.graph.node import BaseNode
from graphs.trader.agents import RiskCheckerAgent, TraderAgent
from modules.context import Context

LOG_DIR = Path("logs/trader_decisions")

def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def _log_dir(context: Context) -> Path:
    tkr = context.get_cache("ticker", "UNKNOWN")
    dt = context.get_cache("trade_date", "UNKNOWN_DATE")
    return LOG_DIR / f"{tkr}_{dt}"


class RiskCheckerNode(BaseNode):
    def __init__(self, name: str = "RiskChecker"):
        super().__init__(name)
        self.agent = RiskCheckerAgent(name=f"{name}")

    def run(self, context: Context) -> Context:
        context = self.agent.run(context)
        self.state = 'passed'

        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            risk_assessment = context.get_cache("risk_assessment", {})
            _write_json(
                _log_dir(context) / f"risk_assessment_{ts}.json",
                {
                    "time": datetime.now().isoformat(),
                    "risk_assessment": risk_assessment,
                },
            )
        except Exception as e:
            print(f"[{self.name}][log]", e)

        risk_assessment = context.get_cache("risk_assessment", {})
        print(f"\n[{self.name}] Risk Assessment:")
        print(f"Risk Level: {risk_assessment.get('risk_level', 'N/A')}")
        print(f"Risk Score: {risk_assessment.get('risk_score', 'N/A')}/100")

        return context


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

        trader_decision = context.get_cache("trader_decision", {})
        risk_assessment = context.get_cache("risk_assessment", {})

        decision = trader_decision.get("decision", "UNKNOWN")
        recommendation = trader_decision.get("recommendation", "No recommendation")
        confidence = trader_decision.get("confidence", 0)

        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            _write_json(
                _log_dir(context) / f"trader_decision_{ts}.json",
                {
                    "time": datetime.now().isoformat(),
                    "trader_decision": trader_decision,
                    "risk_assessment": risk_assessment,
                },
            )
        except Exception as e:
            print(f"[{self.name}][log]", e)

        md = [
            f"# Trading Decision for {ticker}",
            f"**Date**: {trade_date}",
            "",
            "## Final Decision",
            f"**{decision}** (Confidence: {confidence}%)",
            "",
            "## Recommendation",
            recommendation,
            "",
            "## Risk Assessment",
            f"- **Risk Level**: {risk_assessment.get('risk_level', 'N/A')}",
            f"- **Risk Score**: {risk_assessment.get('risk_score', 'N/A')}/100",
            f"- **Risk Factors**: {risk_assessment.get('risk_factors', 'N/A')}",
        ]

        trader_decision_content = "\n".join(md)
        (reports_dir / "trader_decision.md").write_text(trader_decision_content, encoding="utf-8")
        context.set_report("trader_decision", trader_decision_content)

        print(f"\n[{self.name}] Trading Decision:")
        print(f"Decision: {decision} (Confidence: {confidence}%)")
        print(f"Recommendation: {recommendation}")

        return context
