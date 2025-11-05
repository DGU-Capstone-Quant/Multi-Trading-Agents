from modules.agent import Agent
from modules.llm.client import Client
from modules.debate.schemas import BullReply, BearReply, ManagerDecision

COMMON_CONTEXT_TMPL = """[MARKET REPORT]
{market_report}

[SENTIMENT]
{sentiment_report}

[NEWS]
{news_report}

[FUNDAMENTALS]
{fundamentals_report}

[DEBATE HISTORY]
{history}

[LAST OPPONENT ARG]
{last_arg}
"""

class BullResearcher(Agent):
    def __init__(self, name: str = "Bull Analyst"):
        super().__init__()
        self.name = name
        self.llm_client = Client()

    def run(self, **kwargs):
        history = kwargs.get("history", "")
        last_arg = kwargs.get("current_response", "")
        prompt = COMMON_CONTEXT_TMPL.format(
            market_report=kwargs.get("market_report", "N/A"),
            sentiment_report=kwargs.get("sentiment_report", "N/A"),
            news_report=kwargs.get("news_report", "N/A"),
            fundamentals_report=kwargs.get("fundamentals_report", "N/A"),
            history=history,
            last_arg=last_arg,
        )
        contents = [
            "You are a Bull Analyst advocating for investing in the stock.",
            "Debate concisely with strong evidence.",
            prompt,
            "Return JSON with field: chat (your argument)."
        ]
        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=contents,
            thinking_budget=self.quick_thinking_budget,
            schema=BullReply,
        )
        chat = resp.content.get("chat", "")
        line = f"{self.name}: {chat}"
        kwargs["history"] = (history + ("\n" if history else "") + line)
        kwargs["bull_history"] = (kwargs.get("bull_history","") + ("\n" if kwargs.get("bull_history") else "") + line)
        kwargs["current_response"] = line
        kwargs["count"] = kwargs.get("count", 0) + 1
        return kwargs

class BearResearcher(Agent):
    def __init__(self, name: str = "Bear Analyst"):
        super().__init__()
        self.name = name
        self.llm_client = Client()

    def run(self, **kwargs):
        history = kwargs.get("history", "")
        last_arg = kwargs.get("current_response", "")
        prompt = COMMON_CONTEXT_TMPL.format(
            market_report=kwargs.get("market_report", "N/A"),
            sentiment_report=kwargs.get("sentiment_report", "N/A"),
            news_report=kwargs.get("news_report", "N/A"),
            fundamentals_report=kwargs.get("fundamentals_report", "N/A"),
            history=history,
            last_arg=last_arg,
        )
        contents = [
            "You are a Bear Analyst emphasizing risks and downsides.",
            "Debate concisely with strong evidence.",
            prompt,
            "Return JSON with field: chat (your argument)."
        ]
        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=contents,
            thinking_budget=self.quick_thinking_budget,
            schema=BearReply,
        )
        chat = resp.content.get("chat", "")
        line = f"{self.name}: {chat}"
        kwargs["history"] = (history + ("\n" if history else "") + line)
        kwargs["bear_history"] = (kwargs.get("bear_history","") + ("\n" if kwargs.get("bear_history") else "") + line)
        kwargs["current_response"] = line
        kwargs["count"] = kwargs.get("count", 0) + 1
        return kwargs

class ResearchManager(Agent):
    def __init__(self, name: str = "Research Manager"):
        super().__init__()
        self.name = name
        self.llm_client = Client()

    def run(self, **kwargs):
        history = kwargs.get("history","")
        prompt = f"""As the portfolio manager, read the debate below and output a clear decision.

Debate:
{history}

Return JSON with:
- decision: "BUY"|"SELL"|"HOLD"
- rationale: concise reasoning
- plan: concrete next steps
"""
        resp = self.llm_client.generate_content(
            model=self.quick_model,
            contents=[prompt],
            thinking_budget=self.quick_thinking_budget,
            schema=ManagerDecision,
        )
        kwargs["manager_decision"] = resp.content
        kwargs["current_response"] = f"{self.name}: {resp.content}"
        return kwargs
