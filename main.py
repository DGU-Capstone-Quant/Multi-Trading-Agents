from graphs import create_test_graph

"""
test_graph = create_test_graph()
#test_graph.run(subject="어둠의 숲 가설", max_chats=10)
test_graph.run(max_chats=10)
"""

from graphs import create_debate_graph
from pathlib import Path

ticker = "GOOGL"
date = "2025-03-28"
report_fp = Path(f"results/{ticker}/{date}/reports/market_report.md")

graph = create_debate_graph(ticker=ticker, trade_date=date, rounds=4)
graph.run(
    ticker=ticker,
    trade_date=date,
    report_path=str(report_fp),
    report_dir=str(report_fp.parent),
)