# test_debate.py
from graphs.rank import create_rank_graph
from graphs.debate import create_debate_graph
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

# RANK 그래프 실행
print("RANK 실행 중\n")
rank_graph = create_rank_graph()
context = rank_graph.run(context)

recommendation = context.get_cache('recommendation', [])
print(f"Recommendation: {recommendation}\n")

# DEBATE 그래프 실행
print("DEBATE 실행 중\n")
debate_graph = create_debate_graph()
context = debate_graph.run(context)

# 결과 출력
print("\n=== 결과 ===")
for ticker in recommendation:
    plan = context.reports.get(ticker, {}).get("20251101T00", {}).get("investment_plan")
    if plan:
        lines = plan.split('\n')
        decision = [l for l in lines if 'Decision' in l]
        print(f"{ticker}: {decision[0] if decision else 'Plan generated'}")
