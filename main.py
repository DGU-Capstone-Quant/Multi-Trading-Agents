# main.py
from graphs.debate.factory import create_debate_graph, create_context
from graphs.trader.factory import create_trader_graph

if __name__ == "__main__":
    print("=== Starting Debate ===")
    ctx = create_context(
        ticker="GOOGL",
        trade_date="2025-03-28",
        rounds=2
    )

    debate_graph = create_debate_graph(ctx)
    debate_graph.run(ctx)

    print("\n=== Starting Trader ===")
    trader_graph = create_trader_graph()
    trader_graph.run(ctx)