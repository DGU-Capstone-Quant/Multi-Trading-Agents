from graphs import create_test_graph

"""
test_graph = create_test_graph()
#test_graph.run(subject="어둠의 숲 가설", max_chats=10)
test_graph.run(max_chats=10)
"""
from graphs import create_debate_graph

if __name__ == "__main__":
    graph, init_ctx = create_debate_graph(ticker="GOOGL", trade_date="2025-03-28", rounds=2)
    graph.run(**init_ctx)