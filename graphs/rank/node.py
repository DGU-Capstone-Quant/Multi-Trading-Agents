# graphs/rank/node.py
from modules.graph import BaseNode
from modules.context import Context
from .agent import RankAgent
import random

class CandidateNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
    
    def run(self, context: Context) -> Context:
        context.set_cache(recommendation=[], rank_scenario=True)
        tickers = set(context.get_config('tickers', []))
        portfolio = set(context.get_cache('portfolio', {}).keys())
        
        portfolio_size = len(portfolio)
        max_portfolio_size = context.get_config('max_portfolio_size', 5)
        if portfolio_size >= max_portfolio_size:
            self.state = 'passed'
            return context
        
        tickers = list(tickers - portfolio)
        if len(tickers) < 2:
            context.set_cache(recommendation=tickers)
            self.state = 'passed'
            return context

        available_slots = max_portfolio_size - portfolio_size
        if len(tickers) <= available_slots:
            context.set_cache(recommendation=tickers)
            self.state = 'passed'
            return context

        random.shuffle(tickers)
        tickers = tickers[:available_slots * 2]

        context.set_cache(candidates=tickers)
        self.state = 'passed'
        return context
        

class CheckNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
    
    def run(self, context: Context) -> Context:
        candidates = context.get_cache('candidates')
        if not candidates:
            self.state = 'passed'
            return context
        
        date = context.get_cache('date', '20251101T0000')
        no_report_candidates = []
        for ticker in candidates:
            if context.get_report(ticker, date, context.get_config('analysis_tasks', [])[0]):
                continue
            no_report_candidates.append(ticker)

        context.set_cache(no_report_candidates=no_report_candidates)
        self.state = 'passed'
        return context
    

class RankNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.agent = RankAgent()
    
    def _get_combinations(self, candidates: list) -> list:
        combinations = []
        n = len(candidates)
        for i in range(n):
            for j in range(i + 1, n):
                combinations.append((candidates[i], candidates[j]))
        return combinations
    
    def run(self, context: Context) -> Context:
        context.set_cache(rank_scenario=False)
        if context.get_cache('recommendation', []):
            self.state = 'passed'
            return context
        
        candidates = context.get_cache('candidates')
        combinations = self._get_combinations(candidates)
        scores = {ticker: 0 for ticker in candidates}

        for ticker_A, ticker_B in combinations:
            context.set_cache(ticker_A=ticker_A, ticker_B=ticker_B)
            context = self.agent.run(context)
            better_stock = context.get_cache('better_stock', '')
            if better_stock == 'A':
                scores[ticker_A] += 1
            elif better_stock == 'B':
                scores[ticker_B] += 1

        sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        available_slots = context.get_config('max_portfolio_size', 5) - len(context.get_cache('portfolio', {}))
        recommendation = {ticker for ticker, _ in sorted_candidates[:available_slots]}
        recommendation.update(context.get_cache('portfolio', {}).keys())
        context.set_cache(recommendation=list(recommendation))
        self.state = 'passed'
        return context
