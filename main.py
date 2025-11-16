# main.py
from graphs.analyst.graph import create_analyst_graph
from modules.context import Context

context = Context()
context.set_cache(ticker="AAPL")
context.set_config(analysis_tasks = ["financial",])
graph = create_analyst_graph(context)
print()
graph.run(context)
print()
print(context.get_report("financial"))