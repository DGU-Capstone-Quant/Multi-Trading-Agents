# graphs/analyst/node.py
from modules.graph import BaseNode
from modules.context import Context
from .agent import AnalystAgent


class SelectionNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
    
    def run(self, context: Context) -> Context:
        tickers = context.get_cache('tickers', [])
        if not tickers:
            key = 'recommendation' if not context.get_cache('rank_scenario', False) else 'no_report_candidates'
            tickers = context.get_cache(key, [])
            context.set_cache(tickers=tickers)
        
        if not tickers:
            raise ValueError("No tickers available for analysis.")
        
        context.set_cache(ticker=tickers[0])
        tickers = list(tickers[1:])
        context.set_cache(tickers=tickers)
        self.state = 'passed'

        return context

# 병렬 처리 구현 예정
class AnalystNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
        
    def run(self, context: Context) -> Context:
        tasks = context.get_config('analysis_tasks', [])

        for task in tasks:
            agent = AnalystAgent(task=task)
            ticker = context.get_cache('ticker', 'AAPL')
            date = context.get_cache('date', '20251101T0000')
            while not context.get_report(ticker, date, task):
                agent.run(context)

        self.state = 'passed'

        return context