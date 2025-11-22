from modules.agent import Agent
from pydantic import BaseModel, Field
from typing import Literal
from modules.context import Context
import logging

logger = logging.getLogger(__name__)


class RiskAssessment(BaseModel):
    risk_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(..., description="Overall risk level")
    risk_factors: str = Field(..., min_length=20, description="Key risk factors identified")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from 0 (lowest) to 100 (highest)")


class TraderDecision(BaseModel):
    recommendation: str = Field(..., min_length=10, description="Detailed trading recommendation")
    decision: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Final trading decision")
    confidence: int = Field(..., ge=0, le=100, description="Confidence level 0-100")
    quantity: int = Field(..., ge=1, le=1000, description="Recommended quantity to trade (1-1000 shares)")


class RiskCheckerAgent(Agent):
    def __init__(self, name: str = "RiskChecker"):
        super().__init__()
        self.name = name

    def run(self, context: Context) -> Context:
        try:
            logger.info(f"[{self.name}] Starting risk assessment")

            ticker = context.get_cache("ticker", "UNKNOWN")
            date = context.get_cache("date", "UNKNOWN_DATE")

            # investment_plan은 문자열로 저장되므로 직접 가져오기
            from datetime import datetime as dt
            date_key = dt.strptime(date, "%Y%m%dT%H%M").strftime("%Y%m%dT%H")
            investment_plan = context.reports.get(ticker, {}).get(date_key, {}).get("investment_plan", "")

            market_report = context.get_report(ticker, date, "financial")
            if not market_report:
                market_report = context.get_report(ticker, date, "news")
            if not market_report:
                market_report = context.get_report(ticker, date, "fundamental")

            if not investment_plan:
                logger.error(f"[{self.name}] Investment plan not found for {ticker} on {date}")
                raise ValueError("Investment plan is required for risk assessment")

            if not market_report:
                logger.error(f"[{self.name}] Market report not found for {ticker} on {date}")
                raise ValueError("Market report is required for risk assessment")

            system_instruction = """You are a risk analyst evaluating investment risks.
Analyze the investment plan and market conditions to identify potential risks.
Provide a risk level (HIGH/MEDIUM/LOW), key risk factors, and a risk score (0-100)."""

            prompt = f"""Analyze the following investment plan and market conditions for risk assessment.

Investment Plan:
{investment_plan}

Market Report:
{market_report}

Identify potential risks including market volatility, liquidity concerns, valuation risks,
and any other relevant factors. Provide a comprehensive risk assessment."""

            logger.info(f"[{self.name}] Calling LLM for risk assessment")
            resp = self.llm_client.generate_content(
                model=self.quick_model,
                contents=[prompt],
                system_instruction=system_instruction,
                thinking_budget=self.quick_thinking_budget,
                schema=RiskAssessment,
            )

            risk_level = resp.content.get("risk_level", "MEDIUM")
            risk_factors = resp.content.get("risk_factors", "")
            risk_score = resp.content.get("risk_score", 50)

            if not risk_factors:
                logger.error(f"[{self.name}] Empty risk assessment from LLM")
                raise ValueError("LLM returned empty risk assessment")

            logger.info(f"[{self.name}] Risk assessment completed: {risk_level} (score: {risk_score})")

            context.set_cache(
                risk_assessment={
                    "risk_level": risk_level,
                    "risk_factors": risk_factors,
                    "risk_score": risk_score,
                }
            )

            return context

        except Exception as e:
            logger.error(f"[{self.name}] Error during risk assessment: {str(e)}")
            context.set_cache(
                risk_assessment={
                    "risk_level": "HIGH",
                    "risk_factors": f"Error occurred during risk assessment: {str(e)}",
                    "risk_score": 100,
                }
            )
            raise


class TraderAgent(Agent):
    def __init__(self, name: str = "Trader"):
        super().__init__()
        self.name = name

    def run(self, context: Context) -> Context:
        try:
            logger.info(f"[{self.name}] Starting trading decision process")

            ticker = context.get_cache("ticker", "UNKNOWN")
            date = context.get_cache("date", "UNKNOWN_DATE")

            # investment_plan은 문자열로 저장되므로 직접 가져오기
            from datetime import datetime as dt
            date_key = dt.strptime(date, "%Y%m%dT%H%M").strftime("%Y%m%dT%H")
            investment_plan = context.reports.get(ticker, {}).get(date_key, {}).get("investment_plan", "")

            market_report = context.get_report(ticker, date, "financial")
            if not market_report:
                market_report = context.get_report(ticker, date, "news")
            if not market_report:
                market_report = context.get_report(ticker, date, "fundamental")

            risk_assessment = context.get_cache("risk_assessment", {})

            if not investment_plan:
                logger.error(f"[{self.name}] Investment plan not found for {ticker} on {date}")
                raise ValueError("Investment plan is required for trading decision")

            if not market_report:
                logger.error(f"[{self.name}] Market report not found for {ticker} on {date}")
                raise ValueError("Market report is required for trading decision")

            system_instruction = """You are a portfolio manager analyzing market data to make investment decisions.
Based on your analysis, provide a specific recommendation to buy, sell, or hold.
Your decision must be one of: BUY, HOLD, or SELL.
Also provide a confidence level (0-100) and recommended quantity (1-1000 shares) for your decision.

When determining quantity:
- Consider the risk level (HIGH risk = smaller quantity, LOW risk = larger quantity)
- Consider your confidence level (low confidence = smaller quantity)
- Consider portfolio diversification (don't put all eggs in one basket)
- For HOLD decisions, quantity can be any value as it won't be used
- Typical range: 1-10 shares for high risk, 10-50 shares for medium risk, 50-100+ shares for low risk"""

            risk_section = ""
            if risk_assessment:
                risk_section = f"""

Risk Assessment:
- Risk Level: {risk_assessment.get('risk_level', 'UNKNOWN')}
- Risk Score: {risk_assessment.get('risk_score', 'N/A')}/100
- Risk Factors: {risk_assessment.get('risk_factors', 'N/A')}
"""

            prompt = f"""Based on a comprehensive analysis by a team of analysts, here is an investment plan.
This plan incorporates insights from current technical market trends and analysis.
Use this plan as a foundation for evaluating your next trading decision.

Proposed Investment Plan:
{investment_plan}

Current Market Situation:
{market_report}
{risk_section}

Leverage these insights to make an informed and strategic decision.
Provide your recommendation, final decision (BUY/HOLD/SELL), and confidence level (0-100)."""

            logger.info(f"[{self.name}] Calling LLM for trading decision")
            resp = self.llm_client.generate_content(
                model=self.quick_model,
                contents=[prompt],
                system_instruction=system_instruction,
                thinking_budget=self.quick_thinking_budget,
                schema=TraderDecision,
            )

            recommendation = resp.content.get("recommendation", "")
            decision = resp.content.get("decision", "")
            quantity = resp.content.get("quantity", 1)

            if not recommendation or not decision:
                logger.error(f"[{self.name}] Empty response from LLM")
                raise ValueError("LLM returned empty recommendation or decision")

            logger.info(f"[{self.name}] Decision made: {decision}, Quantity: {quantity}")

            context.set_cache(
                trader_decision={
                    "decision": decision,
                    "recommendation": recommendation,
                    "confidence": resp.content.get("confidence", 50),
                    "quantity": quantity,
                }
            )

            return context

        except Exception as e:
            logger.error(f"[{self.name}] Error during trading decision: {str(e)}")
            context.set_cache(
                trader_decision={
                    "decision": "HOLD",
                    "recommendation": f"Error occurred: {str(e)}",
                    "confidence": 0,
                }
            )
            raise
