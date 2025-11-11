# main.py
from graphs.debate.factory import create_debate_graph, create_context

if __name__ == "__main__":
    ctx = create_context(
        ticker="GOOGL",
        trade_date="2025-03-28",
        rounds=2
    )

    graph = create_debate_graph(ctx)

    graph.run(ctx)