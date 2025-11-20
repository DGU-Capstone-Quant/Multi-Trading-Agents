"""토론 상세 보고서 화면"""

from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Container, VerticalScroll
from textual import on

from modules.context import Context
from cli.base import BaseScreen
from cli.components import ReportToggle
from cli.screens.utils import get_report_from_context
from cli.screens.styles import REPORT_TOGGLE_CONTAINER


class DebateDetailScreen(BaseScreen):
    """토론 상세 화면"""

    CSS = f"""
    DebateDetailScreen {{
        layout: vertical;
        background: $surface;
    }}

    #detail-container {{
        layout: vertical;
        height: 1fr;
        padding: 1 2;
    }}

    #detail-header {{
        height: auto;
        background: $boost;
        border: heavy $primary;
        padding: 1 2;
        margin-bottom: 1;
    }}

    #detail-title {{
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }}

    #detail-info {{
        color: $text;
        text-align: center;
        text-style: bold;
    }}

    #reports-container {{
        layout: vertical;
        height: 1fr;
        overflow-y: auto;
        padding: 0 1;
    }}

    #back-button {{
        width: 25;
        height: 3;
        margin: 1 0;
        background: $warning;
        text-style: bold;
    }}

    #back-button:hover {{
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

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="detail-container"):
            with Container(id="detail-header"):
                yield Static("토론 상세 보고서", id="detail-title")
                yield Static(f"Ticker: {self.ticker} | Trade Date: {self.trade_date}", id="detail-info")

            with VerticalScroll(id="reports-container"):
                for title, report_type in [
                    ("시장 분석", "market_report"),
                    ("투자 계획", "investment_plan"),
                    ("트레이더 결정", "trader_decision"),
                ]:
                    report = get_report_from_context(self.context, self.ticker, self.trade_date, report_type)
                    if report:
                        yield ReportToggle(title, report, report_type)

            yield Button("< 뒤로 가기", id="back-button", variant="warning")
        yield Footer()

    @on(Button.Pressed, ".report-toggle-button")
    async def on_toggle_button_pressed(self, event: Button.Pressed) -> None:
        if isinstance(event.button.parent, ReportToggle):
            await event.button.parent.toggle()

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        self.app.pop_screen()

    def action_back(self) -> None:
        self.app.pop_screen()
