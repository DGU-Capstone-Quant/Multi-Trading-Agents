"""거래 내역 위젯"""

from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import VerticalScroll
from textual import on

from cli.base import BaseWidget
from cli.events import ContextUpdated
from cli.screens.utils import build_trade_label, trader_decision_key, trader_recommendation_key


class ActivityWidget(BaseWidget):
    """거래 내역 위젯"""

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

    async def on_context_updated(self, message: ContextUpdated) -> None:
        """컨텍스트가 바뀌면 즉시 새로고침"""
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """거래 내역 목록 새로고침"""
        activity_log = self.query_one("#activity-log", VerticalScroll)
        await activity_log.remove_children()
        entries = self._collect_entries()
        if not entries:
            await activity_log.mount(Static("거래 내역이 없습니다.", classes="activity-item"))
        for idx, entry in enumerate(entries):
            # 각 엔트리에 고유 키를 data-attr로 저장해 디테일 화면 이동에 활용
            button = Button(
                build_trade_label(entry),
                id=None,
                classes="activity-item",
                variant="warning" if entry["is_active"] else "primary",
            )
            button.data = {"ticker": entry["ticker"], "trade_date": entry["trade_date"]}
            await activity_log.mount(button)

    @on(Button.Pressed, ".activity-item")
    def on_activity_clicked(self, event: Button.Pressed) -> None:
        """거래 내역 클릭 - 상세 화면으로 이동"""
        ticker = getattr(event.button, "data", {}).get("ticker")
        trade_date = getattr(event.button, "data", {}).get("trade_date")
        if not ticker or not trade_date:
            return

        is_active = self.context.get_cache(f"trade_progress_{ticker}_{trade_date}", {}).get("status") != "completed"

        if is_active:
            from cli.screens import TradeProgressScreen
            self.app.push_screen(TradeProgressScreen(self.context, ticker, trade_date))
        else:
            from cli.screens import DebateDetailScreen
            self.app.push_screen(DebateDetailScreen(self.context, ticker, trade_date))

    def _collect_entries(self) -> list:
        """거래 내역 수집"""
        entries, seen = [], set()

        for key in self.context.get_cache("trade_progress_keys", []):
            data = self.context.get_cache(key, {})
            if data.get("ticker") and data.get("trade_date"):
                seen.add(f"{data['ticker']}_{data['trade_date']}")
                ticker, trade_date = data["ticker"], data["trade_date"]
                entries.append({
                    "ticker": ticker, "trade_date": trade_date, "status": data.get("status", "completed"),
                    "decision": self.context.get_cache(trader_decision_key(ticker, trade_date), ""),
                    "recommendation": self.context.get_cache(trader_recommendation_key(ticker, trade_date), ""),
                    "is_active": data.get("status") != "completed"
                })

        for debate in self.context.get_cache("completed_debates", []):
            if debate.get("ticker") and debate.get("trade_date") and f"{debate['ticker']}_{debate['trade_date']}" not in seen:
                ticker, trade_date = debate["ticker"], debate["trade_date"]
                entries.append({
                    "ticker": ticker, "trade_date": trade_date, "status": debate.get("status", "completed"),
                    "decision": self.context.get_cache(trader_decision_key(ticker, trade_date), ""),
                    "recommendation": self.context.get_cache(trader_recommendation_key(ticker, trade_date), ""),
                    "is_active": False
                })

        entries.sort(key=lambda x: (x["is_active"], x["trade_date"]), reverse=True)
        return entries
