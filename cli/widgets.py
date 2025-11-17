"""CLI 위젯 모듈 - 모든 위젯 통합"""

from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import VerticalScroll
from textual import on

from cli.base import BaseWidget
from modules.context import Context


class PortfolioWidget(BaseWidget):
    """포트폴리오 보유 종목 표시 위젯"""

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

    async def refresh_data(self) -> None:
        """포트폴리오 종목 목록 새로고침"""
        portfolio_list = self.query_one("#portfolio-list", VerticalScroll)

        # 기존 항목 제거
        for child in list(portfolio_list.children):
            await child.remove()

        # 포트폴리오 ticker 목록 가져오기
        tickers = self.context.get_cache("portfolio", [])
        completed_debates = self.context.get_cache("completed_debates", [])

        if tickers:
            for ticker in tickers:
                # 최근 trade_date 찾기
                ticker_debates = [d for d in completed_debates if d["ticker"] == ticker]
                latest_trade_date = ticker_debates[0]["trade_date"] if ticker_debates else ""

                label = f"{ticker} (최근: {latest_trade_date})" if latest_trade_date else ticker
                await portfolio_list.mount(
                    Button(label, id=f"portfolio-{ticker}", classes="portfolio-item")
                )
        else:
            await portfolio_list.mount(Static("보유 종목 없음", classes="portfolio-item"))

    @on(Button.Pressed, ".portfolio-item")
    def on_portfolio_clicked(self, event: Button.Pressed) -> None:
        """포트폴리오 종목 클릭 시 주가 차트 화면으로 이동"""
        button_id = event.button.id
        if not button_id or not button_id.startswith("portfolio-"):
            return

        ticker = button_id.replace("portfolio-", "")

        from cli.screens import StockChartScreen
        self.app.push_screen(StockChartScreen(self.context, ticker))


class ActivityWidget(BaseWidget):
    """완료된 토론 내역 표시 위젯"""

    CSS = """
    ActivityWidget {
        height: 100%;
    }

    #activity-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        height: 3;
        background: $boost;
        border-bottom: solid $primary;
        content-align: center middle;
    }

    #activity-log {
        height: 1fr;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("완료된 거래", id="activity-title")
        yield VerticalScroll(id="activity-log")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """완료된 토론 목록 새로고침"""
        activity_log = self.query_one("#activity-log", VerticalScroll)

        # 기존 항목 제거
        for child in list(activity_log.children):
            await child.remove()

        # 완료된 토론 가져오기
        completed_debates = self.context.get_cache("completed_debates", [])

        if completed_debates:
            for debate in completed_debates:
                ticker = debate['ticker']
                trade_date = debate['trade_date']
                label = f"{trade_date} - {ticker}"
                button_id = f"debate-{ticker}-{trade_date}"
                await activity_log.mount(
                    Button(label, id=button_id, classes="activity-item")
                )
        else:
            await activity_log.mount(Static("완료된 거래 없음", classes="activity-item"))

    @on(Button.Pressed, ".activity-item")
    def on_activity_clicked(self, event: Button.Pressed) -> None:
        """완료된 토론 클릭 시 상세 화면으로 이동"""
        button_id = event.button.id
        if not button_id or not button_id.startswith("debate-"):
            return

        parts = button_id.replace("debate-", "").split("-")
        if len(parts) < 2:
            return

        ticker = parts[0]
        trade_date = "-".join(parts[1:])

        from cli.screens import DebateDetailScreen
        self.app.push_screen(DebateDetailScreen(self.context, ticker, trade_date))
