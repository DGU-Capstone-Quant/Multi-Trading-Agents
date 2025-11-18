from modules.agent import Agent
from modules.llm.client import Client
from pydantic import BaseModel
from modules.context import Context


class TraderDecision(BaseModel):
    recommendation: str
    decision: str


class TraderAgent(Agent):
    def __init__(self, name: str = "Trader"):
        super().__init__()
        self.name = name
        self.llm_client = Client()

    def run(self, context: Context) -> Context:
        investment_plan = context.get_report("investment_plan")
        market_report = context.get_report("market_report")

        system_instruction = f"""You are a portfolio manager analyzing market data to make investment decisions.
Based on your analysis, provide a specific recommendation to buy, sell, or hold.
End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation."""

        prompt = f"""Based on a comprehensive analysis by a team of analysts, here is an investment plan.
This plan incorporates insights from current technical market trends and analysis.
Use this plan as a foundation for evaluating your next trading decision.

Proposed Investment Plan:
{investment_plan}

Current Market Situation:
{market_report}

Leverage these insights to make an informed and strategic decision.
Provide your recommendation and final decision (BUY/HOLD/SELL)."""

        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=[prompt],
            system_instructions=system_instruction,
            thinking_budget=self.quick_thinking_budget,
            schema=TraderDecision,
        )

        recommendation = resp.content.get("recommendation", "")
        decision = resp.content.get("decision", "")

        context.set_cache(
            trader_recommendation=recommendation,
            trader_decision=decision,
            trader_full_response=f"{self.name}: {recommendation}\nDECISION: {decision}",
        )

        return context
