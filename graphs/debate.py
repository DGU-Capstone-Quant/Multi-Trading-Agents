# graphs/debate.py
from __future__ import annotations

from pathlib import Path
from typing import Dict

from modules.graph.graph import Graph
from modules.debate.nodes import BullNode, BearNode, ManagerNode

def _report_path(ticker: str, trade_date: str) -> Path:
    return Path("results") / ticker / trade_date / "reports" / "market_report.md"


def _read_report(ticker: str, trade_date: str) -> str:
    fp = _report_path(ticker, trade_date)
    if not fp.exists():
        raise FileNotFoundError(
            f"[debate] market_report.md not found:\n - {fp}\n"
            f"Create the file at this location. ex)\n"
            f"  results/{ticker}/{trade_date}/reports/market_report.md"
        )
    return fp.read_text(encoding="utf-8")

def _under_round_limit_factory(max_rounds: int):
    def _under(**kwargs) -> bool:
        return kwargs.get("count", 0) < max_rounds * 2
    return _under

def _reached_round_limit_factory(max_rounds: int):
    under = _under_round_limit_factory(max_rounds)
    return lambda **kwargs: not under(**kwargs)

def create_debate_graph(
    ticker: str,
    trade_date: str,
    rounds: int = 1,
    *,
    sentiment_report: str = "(auto) none",
    news_report: str = "(auto) none",
    fundamentals_report: str = "(auto) none",
) -> Graph:
    bull = BullNode()
    bear = BearNode()
    mgr  = ManagerNode()

    g = Graph(bull)
    g.add_node(bear)
    g.add_node(mgr)

    g.add_edge("Bull", "Bear")
    g.add_edge("Bear", "Bull",    cond_func=_under_round_limit_factory(rounds))
    g.add_edge("Bear", "Manager", cond_func=_reached_round_limit_factory(rounds))

    report_fp = _report_path(ticker, trade_date)
    g.default_kwargs = {
        "ticker": ticker,
        "trade_date": trade_date,
        "market_report": _read_report(ticker, trade_date),
        "report_path": str(report_fp),
        "report_dir": str(report_fp.parent),
        "sentiment_report": sentiment_report,
        "news_report": news_report,
        "fundamentals_report": fundamentals_report,
        "history": "",
        "bull_history": "",
        "bear_history": "",
        "current_response": "",
        "count": 0,
    }
    return g
