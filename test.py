from graphs import create_test_graph
from modules.context import Context

context = Context()
context.set_cache(subject="어둠의 숲 가설", max_chats=10)
test_graph = create_test_graph()
test_graph.run(context)