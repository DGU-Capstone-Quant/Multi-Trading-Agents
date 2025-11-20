"""포트폴리오 위젯"""

from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import VerticalScroll
from textual import on

from cli.base import BaseWidget
from cli.events import ContextUpdated


class PortfolioWidget(BaseWidget):
    """포트폴리오 종목 목록 위젯"""

    CSS = """
    PortfolioWidget {
        height: 100%;
    }

    #portfolio-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        height: 3;
        background: $boost;
        border-bottom: solid $primary;
        content-align: center middle;
    }

    #portfolio-list {
        height: 1fr;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("보유 포트폴리오", id="portfolio-title")
        yield VerticalScroll(id="portfolio-list")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_context_updated(self, message: ContextUpdated) -> None:
        """컨텍스트가 바뀌면 즉시 새로고침"""
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """포트폴리오 종목 목록 새로고침"""
        portfolio_list = self.query_one("#portfolio-list", VerticalScroll)
        await portfolio_list.remove_children()
        portfolio_data = self.context.get_cache("portfolio", {}) or {}
        if isinstance(portfolio_data, dict):
            tickers = sorted(portfolio_data.keys())
        elif isinstance(portfolio_data, (list, set, tuple)):
            tickers = list(portfolio_data)
        else:
            tickers = []
        for ticker in (tickers or ["보유 종목 없음"]):
            widget = Button(ticker, id=None, classes="portfolio-item") if tickers else Static(ticker, classes="portfolio-item")
            await portfolio_list.mount(widget)

    @on(Button.Pressed, ".portfolio-item")
    def on_portfolio_clicked(self, event: Button.Pressed) -> None:
        """포트폴리오 종목 클릭 - 주가 차트 화면으로 이동"""
        # ID를 설정하지 않으므로 라벨에서 티커를 읽어 이동
        from cli.screens import StockChartScreen
        self.app.push_screen(StockChartScreen(self.context, event.button.label))
