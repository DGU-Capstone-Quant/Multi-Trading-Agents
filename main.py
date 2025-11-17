# main.py
from graphs.rank import create_rank_graph
from modules.context import Context

context = Context()
context.set_config(
    analysis_tasks=["financial",],
    tickers=["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
    max_portfolio_size=3,
)

context.set_cache(
    date="20251101T0000",
)

rank_graph = create_rank_graph()

rank_graph.run(context)