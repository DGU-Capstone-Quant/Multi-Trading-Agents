"""거래 내역 위젯"""

from textual.app import ComposeResult
from textual.widgets import Static, Markdown, Collapsible
from textual.containers import VerticalScroll
from textual import on

from cli.base import BaseWidget
from cli.events import ContextUpdated


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_log_len: int = 0

    def compose(self) -> ComposeResult:
        yield Static("거래 로그", id="activity-title")
        yield VerticalScroll(id="activity-log")
    
    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_context_updated(self, message: ContextUpdated) -> None:
        await self.refresh_data()

    async def refresh_data(self) -> None:
        logs = self.context.logs or []

        if len(logs) == self._last_log_len:
            return
        self._last_log_len = len(logs)

        activity_log = self.query_one("#activity-log", VerticalScroll)
        await activity_log.remove_children()

        if not logs:
            await activity_log.mount(Static("로그 존재 X", classes="activity-item"))
            return

        for log in reversed(logs):
            summary = log.get("summary", "")
            content = log.get("content", "")

            if content:
                collapsible = Collapsible(
                    Markdown(content),
                    title=summary,
                    collapsed=True
                )
                await activity_log.mount(collapsible)
            else:
                await activity_log.mount(Static(summary, classes="activity-item"))

            
