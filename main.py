# main.py
from graphs.main import create_main_graph
from modules.context import Context

# Context 설정
context = Context()
context.set_config(
    analysis_tasks=["financial",],
    tickers=["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
    max_portfolio_size=1,
    rounds=2,
)

context.set_cache(
    date="20251101T0000",
)

graph = create_main_graph()
context = graph.run(context)