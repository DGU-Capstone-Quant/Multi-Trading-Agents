# graphs/debate/factory.py
from pathlib import Path
from modules.graph.graph import Graph
from graphs.debate.nodes import BullNode, BearNode, ManagerNode


def _report_path(ticker: str, trade_date: str) -> Path:
    return Path("results") / ticker / trade_date / "reports" / "market_report.md"


def _read_report(ticker: str, trade_date: str) -> str:
    fp = _report_path(ticker, trade_date)
    if not fp.exists():
        raise FileNotFoundError(f"market_report.md not found: {fp}")
    return fp.read_text(encoding="utf-8")


def _under_round_limit_factory(max_rounds: int):
    def _under(**kw): 
        return kw.get("count", 0) < max_rounds * 2
    return _under


def _reached_round_limit_factory(max_rounds: int):
    under = _under_round_limit_factory(max_rounds)
    return lambda **kw: not under(**kw)


def create_debate_graph(ticker: str, trade_date: str, rounds: int = 1):
    """
    그래프 객체와 초기 kwargs를 튜플로 반환.
    사용:
        graph, init_ctx = create_debate_graph("GOOGL", "2025-03-28", rounds=4)
        graph.run(**init_ctx)
    """
    bull = BullNode()
    bear = BearNode()
    mgr = ManagerNode()

    g = Graph(bull)
    g.add_node(bear)
    g.add_node(mgr)

    g.add_edge("Bull", "Bear")
    g.add_edge("Bear", "Bull", cond_func=_under_round_limit_factory(rounds))
    g.add_edge("Bear", "Manager", cond_func=_reached_round_limit_factory(rounds))

    rp = _report_path(ticker, trade_date)
    init_ctx = {
        "ticker": ticker,
        "trade_date": trade_date,
        "market_report": _read_report(ticker, trade_date),
        "report_path": str(rp),
        "report_dir": str(rp.parent),
        "sentiment_report": "(auto) none",
        "news_report": "(auto) none",
        "fundamentals_report": "(auto) none",
        "history": "",
        "bull_history": "",
        "bear_history": "",
        "current_response": "",
        "count": 0,
    }
    return g, init_ctx
