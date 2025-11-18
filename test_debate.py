from graphs.debate.factory import run_debate
from modules.context import Context

context = Context()
context.set_config(
    analysis_tasks=["financial"],
    tickers=["GOOGL", "AAPL"],
    rounds=2,
)

context.set_cache(
    date="20250328T0930",
)

# 테스트용 리포트 설정 (실제로는 analyst가 생성)
for ticker in context.get_config("tickers"):
    context.set_report(
        ticker,
        context.get_cache("date"),
        "financial",
        f"{ticker} financial analysis: Strong revenue growth."
    )

debate_context = run_debate(context)
