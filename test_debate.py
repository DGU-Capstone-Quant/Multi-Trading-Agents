# test_debate.py
from graphs.debate.factory import create_context, create_debate_graph

context = create_context(ticker="GOOGL", trade_date="20250328T0930", rounds=2)
debate_graph = create_debate_graph(context)
context = debate_graph.run(context)

history = context.get_cache("history", "")
print(f"\n{history}\n")

decision = context.get_cache("manager_decision", {})
print("-" * 80)
print(f"Decision: {decision.get('decision', 'N/A')}")
print(f"Rationale: {decision.get('rationale', 'N/A')}")
print(f"Plan: {decision.get('plan', 'N/A')}")
print("=" * 80)
