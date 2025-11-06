# modules/debate/nodes.py
from datetime import datetime
import json
from pathlib import Path

from modules.graph.node import BaseNode
from modules.debate.agents import BullResearcher, BearResearcher, ResearchManager

LOG_DIR = Path("logs/research_dialogs")
RESULTS_DIR = Path("results")

def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _round_dir(kwargs) -> Path:
    ticker = kwargs.get("ticker", "UNKNOWN")
    trade_date = kwargs.get("trade_date", "UNKNOWN_DATE")
    return LOG_DIR / f"{ticker}_{trade_date}"


class BullNode(BaseNode):
    def __init__(self):
        super().__init__("Bull")
        self.agent = BullResearcher()

    def run(self, **kwargs):
        kwargs = self.agent.run(**kwargs)
        self.state = "passed"
        try:
            rd = _round_dir(kwargs)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = rd / f"bull_round_{kwargs.get('count')}_{ts}.json"
            _write_json(fp, {
                "time": datetime.now().isoformat(),
                "kwargs": {k: kwargs[k] for k in ["history", "current_response", "count"] if k in kwargs}
            })
        except Exception as e:
            print("[BullNode][log]", e)
        return kwargs


class BearNode(BaseNode):
    def __init__(self):
        super().__init__("Bear")
        self.agent = BearResearcher()

    def run(self, **kwargs):
        kwargs = self.agent.run(**kwargs)
        self.state = "passed"
        try:
            rd = _round_dir(kwargs)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = rd / f"bear_round_{kwargs.get('count')}_{ts}.json"
            _write_json(fp, {
                "time": datetime.now().isoformat(),
                "kwargs": {k: kwargs[k] for k in ["history", "current_response", "count"] if k in kwargs}
            })
        except Exception as e:
            print("[BearNode][log]", e)
        return kwargs


class ManagerNode(BaseNode):
    def __init__(self):
        super().__init__("Manager")
        self.agent = ResearchManager()

    def run(self, **kwargs):
        kwargs = self.agent.run(**kwargs)
        self.state = "passed"

        try:
            rd = _round_dir(kwargs)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            _write_json(
                rd / f"manager_decision_{ts}.json",
                {"time": datetime.now().isoformat(), "decision": kwargs.get("manager_decision")}
            )
        except Exception as e:
            print("[ManagerNode][log]", e)

        try:
            report_dir = kwargs.get("report_dir")
            if report_dir:
                reports_dir = Path(report_dir)
            else:
                report_path = kwargs.get("report_path")
                if report_path:
                    reports_dir = Path(report_path).parent
                else:
                    reports_dir = (RESULTS_DIR
                                   / kwargs.get("ticker", "UNKNOWN")
                                   / kwargs.get("trade_date", "UNKNOWN_DATE")
                                   / "reports")

            reports_dir.mkdir(parents=True, exist_ok=True)

            plan = kwargs.get("manager_decision") or {}
            decision = plan.get("decision", "")
            rationale = plan.get("rationale", "")
            plan_body = plan.get("plan", "")

            md = [
                f"# Investment Plan ({kwargs.get('ticker','UNKNOWN')} / {kwargs.get('trade_date','UNKNOWN_DATE')})",
                "",
                f"**Decision:** {decision}",
                "",
                "## Rationale",
                rationale,
                "",
                "## Plan",
                plan_body,
            ]
            (reports_dir / "investment_plan.md").write_text("\n".join(md), encoding="utf-8")
        except Exception as e:
            print("[ManagerNode][save plan]", e)

        return kwargs
