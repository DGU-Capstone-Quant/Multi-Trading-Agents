"""실시간 거래 진행 상황 화면 (로그 기반)"""

from datetime import datetime
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Container, VerticalScroll
from textual import on

from modules.context import Context
from cli.base import BaseScreen
from cli.screens.utils import (
    format_status_text,
    trader_decision_key,
    trader_recommendation_key,
)


class TradeProgressScreen(BaseScreen):
    """실시간 거래 진행 상황 화면"""

    CSS = """
    TradeProgressScreen {
        layout: vertical;
        background: $surface;
    }

    #progress-container {
        layout: vertical;
        height: 1fr;
        padding: 1 2;
    }

    #progress-header {
        height: auto;
        background: $boost;
        border: heavy $primary;
        padding: 1 2;
        margin-bottom: 1;
    }

    #progress-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }

    #progress-status {
        color: $text;
        text-align: center;
    }

    #logs-container {
        layout: vertical;
        height: 1fr;
        overflow-y: auto;
        padding: 0 1;
    }

    .log-item {
        margin: 0 0 1 0;
        padding: 1 2;
        background: $panel;
        border: solid $primary;
        color: $text;
        text-align: left;
    }

    .log-empty {
        color: $text;
        text-align: center;
        padding: 1;
    }

    #progress-back-button {
        width: 25;
        height: 3;
        margin: 1 0;
        background: $warning;
        text-style: bold;
    }

    #progress-back-button:hover {
        background: $error;
        color: $text;
    }
    """

    BINDINGS = [("escape", "back", "뒤로 가기")]

    def __init__(self, context: Context, ticker: str, trade_date: str, *args, **kwargs):
        super().__init__(context, *args, **kwargs)
        self.ticker = ticker
        self.trade_date = trade_date

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="progress-container"):
            with Container(id="progress-header"):
                yield Static(f"거래 진행 상황 · {self.trade_date} / {self.ticker}", id="progress-title")
            yield Static("", id="progress-status")

            with VerticalScroll(id="logs-container"):
                yield Static("로그를 불러오는 중입니다...", classes="log-empty")

            yield Button("< 뒤로 가기", id="progress-back-button", variant="warning")
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_content()
        self.set_interval(2.0, self.refresh_content)

    async def refresh_content(self) -> None:
        data = self._get_progress_data()
        self.query_one("#progress-status", Static).update(format_status_text(data.get("status", "")))
        await self.refresh_logs()

    async def refresh_logs(self) -> None:
        container = self.query_one("#logs-container", VerticalScroll)
        await container.remove_children()

        logs = getattr(self.context, "logs", []) or []
        # 티커 관련 로그만 우선 표시, 없으면 전체 로그
        def _match_ticker(log: dict) -> bool:
            summary = (log.get("summary") or "").upper()
            content = (log.get("content") or "").upper()
            return self.ticker.upper() in summary or self.ticker.upper() in content

        matched = [l for l in logs if _match_ticker(l)]
        view_logs = matched if matched else logs

        if not view_logs:
            await container.mount(Static("로그가 없습니다.", classes="log-empty"))
            return

        # 최신 로그 먼저 표시. timestamp 없는 경우도 안전하게 처리
        def _key(log: dict) -> float:
            ts = log.get("timestamp")
            try:
                return float(ts)
            except Exception:
                return 0.0

        for log in sorted(view_logs, key=_key, reverse=True):
            ts = log.get("timestamp")
            try:
                ts_text = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else ""
            except Exception:
                ts_text = str(ts) if ts else ""

            summary = log.get("summary", "")
            content = log.get("content", "")
            lines = [f"[{ts_text}] {summary}".strip()]
            if content:
                lines.append(content)
            await container.mount(Static("\n".join(lines), classes="log-item"))

    def _get_progress_data(self) -> dict:
        trade_date = (self.trade_date or "").strip() or self.context.get_cache("trade_date", "")
        decision = ""
        recommendation = ""

        if trade_date:
            decision = self.context.get_cache(trader_decision_key(self.ticker, trade_date), "") or self.context.get_cache("trader_decision", "")
            recommendation = self.context.get_cache(trader_recommendation_key(self.ticker, trade_date), "") or self.context.get_cache("trader_recommendation", "")
        else:
            decision = self.context.get_cache("trader_decision", "")
            recommendation = self.context.get_cache("trader_recommendation", "")

        status = "completed" if decision else "in_progress"
        return {
            "ticker": self.ticker.strip().upper(),
            "trade_date": trade_date,
            "status": status,
            "decision": decision,
            "recommendation": recommendation,
        }

    @on(Button.Pressed, "#progress-back-button")
    def on_back_pressed(self) -> None:
        self.app.pop_screen()

    def action_back(self) -> None:
        self.app.pop_screen()
