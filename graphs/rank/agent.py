# graphs/rank/agent.py
from modules.agent import Agent
from modules.context import Context
from pydantic import BaseModel
from .schema import ComparisonSchema


# RankAgent: 두 종목의 보고서들을 비교하여 더 유망한 종목을 선택하는 에이전트
class RankAgent(Agent):
    def __init__(self):
        super().__init__()
    
    def _create(self, contents: list, schema: BaseModel=None, deep: bool=False):
        model = self.deep_model if deep else self.quick_model
        thinking_budget = self.deep_thinking_budget if deep else self.quick_thinking_budget

        system_instruction = None

        return self.llm_client.generate_content(
            model=model,
            contents=contents,
            system_instruction=system_instruction,
            thinking_budget=thinking_budget,
            schema=schema,
        )
    
    def run(self, context: Context) -> Context:
        ticker_A = context.get_cache("ticker_A", "")
        ticker_B = context.get_cache("ticker_B", "")
        if not ticker_A or not ticker_B:
            raise ValueError("Both ticker_A and ticker_B must be provided in the context cache.")
        
        tasks = context.get_config('analysis_tasks', [])
        contents = [f"Compare the analysis reports of two stocks: {ticker_A}(A) and {ticker_B}(B)."]
        date = context.get_cache("date", "20251101T0000")
        for task in tasks:
            report_A = context.get_report(ticker_A, date, task)
            report_B = context.get_report(ticker_B, date, task)
            contents.append(f"Report for {ticker_A} on {task}:\n{report_A}\n")
            contents.append(f"Report for {ticker_B} on {task}:\n{report_B}\n")
        contents.append("Based on the above reports, determine which stock is more promising and provide a detailed explanation.")

        res = self._create(
            contents=contents,
            schema=ComparisonSchema,
        )

        chosen = res.content.get("better_stock", "")
        if chosen not in ['A', 'B']:
            raise ValueError("The better_stock field must be either 'A' or 'B'.")
        
        context.set_cache(better_stock=chosen)
        return context
        
        
