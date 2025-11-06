# graphs/debate/nodes.py
from datetime import datetime
from pathlib import Path
import json

from modules.graph.node import BaseNode
from graphs.debate.agents import BullResearcher, BearResearcher, ResearchManager

LOG_DIR = Path("logs/research_dialogs")
RESULTS_DIR = Path("results")


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _round_dir(kw) -> Path:
    return LOG_DIR / f"{kw.get('ticker','UNKNOWN')}_{kw.get('trade_date','UNKNOWN_DATE')}"


class BullNode(BaseNode):
    def __init__(self):
        super().__init__("Bull")
        self.agent = BullResearcher()

    def run(self, **kw):
        kw = self.agent.run(**kw)
        self.state = 'passed'
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            _write_json(
                _round_dir(kw) / f"bull_round_{kw.get('count')}_{ts}.json",
                {
                    "time": datetime.now().isoformat(),
                    "history_tail": kw.get("current_response", ""),
                    "count": kw.get("count", 0),
                },
            )
        except Exception as e:
            print("[BullNode][log]", e)
        return kw


class BearNode(BaseNode):
    def __init__(self):
        super().__init__("Bear")
        self.agent = BearResearcher()

    def run(self, **kw):
        kw = self.agent.run(**kw)
        self.state = 'passed'
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            _write_json(
                _round_dir(kw) / f"bear_round_{kw.get('count')}_{ts}.json",
                {
                    "time": datetime.now().isoformat(),
                    "history_tail": kw.get("current_response", ""),
                    "count": kw.get("count", 0),
                },
            )
        except Exception as e:
            print("[BearNode][log]", e)
        return kw


class ManagerNode(BaseNode):
    def __init__(self):
        super().__init__("Manager")
        self.agent = ResearchManager()

    def run(self, **kw):
        kw = self.agent.run(**kw)
        self.state = 'passed'

        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            _write_json(
                _round_dir(kw) / f"manager_decision_{ts}.json",
                {"time": datetime.now().isoformat(), "decision": kw.get("manager_decision")},
            )
        except Exception as e:
            print("[ManagerNode][log]", e)

        try:
            if kw.get("report_dir"):
                reports_dir = Path(kw["report_dir"])
            elif kw.get("report_path"):
                reports_dir = Path(kw["report_path"]).parent
            else:
                reports_dir = (
                    RESULTS_DIR
                    / kw.get("ticker", "UNKNOWN")
                    / kw.get("trade_date", "UNKNOWN_DATE")
                    / "reports"
                )
            reports_dir.mkdir(parents=True, exist_ok=True)

            plan = kw.get("manager_decision") or {}
            md = [
                f"# Investment Plan ({kw.get('ticker','UNKNOWN')} / {kw.get('trade_date','UNKNOWN_DATE')})",
                "",
                f"**Decision:** {plan.get('decision','')}",
                "",
                "## Rationale",
                plan.get("rationale", ""),
                "",
                "## Plan",
                plan.get("plan", ""),
            ]
            (reports_dir / "investment_plan.md").write_text("\n".join(md), encoding="utf-8")
        except Exception as e:
            print("[ManagerNode][save plan]", e)

        return kw