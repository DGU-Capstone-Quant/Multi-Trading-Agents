"""CLI 위젯 모듈"""

from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import VerticalScroll
from textual import on

from cli.base import BaseWidget
from modules.context import Context


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

    async def refresh_data(self) -> None:
        """포트폴리오 종목 목록 새로고침"""
        portfolio_list = self.query_one("#portfolio-list", VerticalScroll)

        for child in list(portfolio_list.children):
            await child.remove()

        tickers = self.context.get_cache("portfolio", [])

        if tickers:
            for ticker in tickers:
                await portfolio_list.mount(Button(ticker, id=f"portfolio-{ticker}", classes="portfolio-item"))
        else:
            await portfolio_list.mount(Static("보유 종목 없음", classes="portfolio-item"))

    @on(Button.Pressed, ".portfolio-item")
    def on_portfolio_clicked(self, event: Button.Pressed) -> None:
        """포트폴리오 종목 클릭 처리 - 주가 차트 화면으로 이동"""
        button_id = event.button.id
        if not button_id or not button_id.startswith("portfolio-"):
            return

        ticker = button_id.replace("portfolio-", "")
        from cli.screens import StockChartScreen
        self.app.push_screen(StockChartScreen(self.context, ticker))


class ActivityWidget(BaseWidget):
    """거래 내역 위젯 (진행 중 + 완료)"""

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
        yield Static("거래 내역", id="activity-title")
        yield VerticalScroll(id="activity-log")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """거래 내역 목록 새로고침"""
        activity_log = self.query_one("#activity-log", VerticalScroll)

        for child in list(activity_log.children):
            await child.remove()

        entries = self._collect_trade_entries()

        if not entries:
            await activity_log.mount(Static("거래 내역이 없습니다.", classes="activity-item"))
            return

        for idx, entry in enumerate(entries):
            # 고유한 ID 생성 (ticker, trade_date, 인덱스 조합)
            button_id = f"activity-{entry['ticker']}-{entry['trade_date']}-{idx}"
            label = self._build_trade_label(entry)
            variant = "warning" if entry["is_active"] else "primary"
            await activity_log.mount(Button(label, id=button_id, classes="activity-item", variant=variant))

    @on(Button.Pressed, ".activity-item")
    def on_activity_clicked(self, event: Button.Pressed) -> None:
        """거래 내역 항목 선택 시 화면 이동"""
        button_id = event.button.id
        if not button_id or not button_id.startswith("activity-"):
            return

        # ID 형식: activity-{ticker}-{trade_date}-{idx}
        parts = button_id.replace("activity-", "").rsplit("-", 1)
        if len(parts) != 2:
            return

        ticker_date = parts[0]
        # ticker와 trade_date 분리 (trade_date는 YYYY-MM-DD 형식)
        parts2 = ticker_date.split("-")
        if len(parts2) < 4:  # ticker-YYYY-MM-DD 최소 4개 부분
            return

        ticker = parts2[0]
        trade_date = "-".join(parts2[1:])

        # 진행 중인지 완료된 것인지 확인
        progress_key = f"trade_progress_{ticker}_{trade_date}"
        progress_data = self.context.get_cache(progress_key, {})
        is_active = progress_data.get("status") != "completed" if progress_data else False

        if is_active:
            from cli.screens import TradeProgressScreen
            self.app.push_screen(TradeProgressScreen(self.context, ticker, trade_date))
        else:
            from cli.screens import DebateDetailScreen
            self.app.push_screen(DebateDetailScreen(self.context, ticker, trade_date))

    def _collect_trade_entries(self) -> list:
        """Context에서 거래 내역 수집 (진행 중 + 완료)"""
        entries = []
        seen = set()
        progress_keys = self.context.get_cache("trade_progress_keys", [])

        # 진행 중인 거래 수집
        for key in progress_keys:
            data = self.context.get_cache(key, {})
            ticker = data.get("ticker")
            trade_date = data.get("trade_date")
            if not ticker or not trade_date:
                continue

            seen.add(f"{ticker}_{trade_date}")
            entries.append({
                "ticker": ticker,
                "trade_date": trade_date,
                "status": data.get("status", "progress"),
                "decision": data.get("decision", ""),
                "recommendation": data.get("recommendation", ""),
                "is_active": data.get("status") != "completed",
            })

        # 완료된 거래 수집
        completed_debates = self.context.get_cache("completed_debates", [])
        for debate in completed_debates:
            ticker = debate.get("ticker")
            trade_date = debate.get("trade_date")
            if not ticker or not trade_date:
                continue

            trade_id = f"{ticker}_{trade_date}"
            if trade_id in seen:
                continue

            entries.append({
                "ticker": ticker,
                "trade_date": trade_date,
                "status": "completed",
                "decision": self.context.get_cache(f"{ticker}_{trade_date}_trader_decision", ""),
                "recommendation": self.context.get_cache(f"{ticker}_{trade_date}_trader_recommendation", ""),
                "is_active": False,
            })

        entries.sort(key=lambda x: (x["is_active"], x["trade_date"]), reverse=True)
        return entries

    def _build_trade_label(self, entry: dict) -> str:
        """거래 내역 라벨 생성"""
        status = entry.get("status", "")
        if status == "debate_in_progress":
            status_label = "토론 진행 중"
        elif status == "plan_ready":
            status_label = "트레이더 검토 중"
        elif status == "completed":
            status_label = entry.get("decision") or "거래 완료"
        else:
            status_label = "준비 중"

        return f"{entry['trade_date']} - {entry['ticker']} ({status_label})"
