# main.py
from graphs.debate.factory import create_debate_graph

if __name__ == "__main__":
    graph, ctx = create_debate_graph(
        ticker="GOOGL",
        trade_date="2025-03-28",
        rounds=2
    )

    graph.run(ctx)