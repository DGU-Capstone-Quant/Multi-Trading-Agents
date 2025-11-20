"""실시간 거래 진행 상황 화면"""

from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Container, VerticalScroll
from textual import on

from modules.context import Context
from cli.base import BaseScreen
from cli.components import ReportToggle
from cli.screens.utils import (
    make_progress_key,
    format_status_text,
    get_report_from_context,
    trader_decision_key,
    trader_recommendation_key,
)
from cli.screens.styles import REPORT_TOGGLE_CONTAINER


class TradeProgressScreen(BaseScreen):
    """실시간 거래 진행 상황 화면"""

    CSS = f"""
    TradeProgressScreen {{
        layout: vertical;
        background: $surface;
    }}

    #progress-container {{
        layout: vertical;
        height: 1fr;
        padding: 1 2;
    }}

    #progress-header {{
        height: auto;
        background: $boost;
        border: heavy $primary;
        padding: 1 2;
        margin-bottom: 1;
    }}

    #progress-title {{
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }}

    #progress-status {{
        color: $text;
        text-align: center;
    }}

    #reports-container {{
        layout: vertical;
        height: 1fr;
        overflow-y: auto;
        padding: 0 1;
    }}

    #progress-back-button {{
        width: 25;
        height: 3;
        margin: 1 0;
        background: $warning;
        text-style: bold;
    }}

    #progress-back-button:hover {{
        background: $error;
        color: $text;
    }}

    {REPORT_TOGGLE_CONTAINER}
    """

    BINDINGS = [("escape", "back", "뒤로 가기")]

    def __init__(self, context: Context, ticker: str, trade_date: str, *args, **kwargs):
        super().__init__(context, *args, **kwargs)
        self.ticker = ticker
        self.trade_date = trade_date
        self.toggles = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="progress-container"):
            with Container(id="progress-header"):
                yield Static(f"거래 진행 상황 · {self.trade_date} / {self.ticker}", id="progress-title")
            yield Static("", id="progress-status")

            with VerticalScroll(id="reports-container"):
                for title, key, default_msg in [
                    ("시장 분석", "market_report", "시장 분석을 진행 중입니다."),
                    ("투자 계획", "investment_plan", "투자 계획을 생성 중입니다."),
                    ("트레이더 결정", "trader_decision", "트레이더 결정 대기 중입니다."),
                ]:
                    toggle = ReportToggle(title, default_msg, f"tp_{key}")
                    self.toggles[key] = toggle
                    yield toggle

            yield Button("< 뒤로 가기", id="progress-back-button", variant="warning")
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_content()
        self.set_interval(2.0, self.refresh_content)

    async def refresh_content(self) -> None:
        data = self._get_progress_data()
        self.query_one("#progress-status", Static).update(format_status_text(data.get("status", "")))

        for key, toggle in self.toggles.items():
            if key == "trader_decision" and (data.get("decision") or data.get("recommendation")):
                content = f"**결정:** {data.get('decision','')}\n\n**추천:**\n{data.get('recommendation','')}"
            else:
                content = data.get(key) or f"{key.replace('_', ' ').title()}을 사용할 수 없습니다."
            toggle.set_content(content)

    def _get_progress_data(self) -> dict:
        decision = self.context.get_cache(trader_decision_key(self.ticker, self.trade_date), "")
        data = self.context.get_cache(make_progress_key(self.ticker, self.trade_date), {}) or {
            "ticker": self.ticker, "trade_date": self.trade_date, "status": "completed" if decision else "unknown"
        }
        data.update({
            "market_report": get_report_from_context(self.context, self.ticker, self.trade_date, "market_report"),
            "investment_plan": get_report_from_context(self.context, self.ticker, self.trade_date, "investment_plan"),
            "decision": decision,
            "recommendation": self.context.get_cache(trader_recommendation_key(self.ticker, self.trade_date), ""),
        })
        return data

    @on(Button.Pressed, "#progress-back-button")
    def on_back_pressed(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, ".report-toggle-button")
    async def on_toggle_button_pressed(self, event: Button.Pressed) -> None:
        if isinstance(event.button.parent, ReportToggle):
            await event.button.parent.toggle()

    def action_back(self) -> None:
        self.app.pop_screen()
