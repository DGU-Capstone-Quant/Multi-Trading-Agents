"""트레이딩 대시보드 애플리케이션"""

from textual.app import App

from modules.context import Context
from cli.screens import MainScreen


class TradingDashboardApp(App):
    """멀티 트레이딩 에이전트 대시보드"""

    TITLE = "멀티 트레이딩 에이전트 대시보드"

    BINDINGS = [
        ("q", "quit", "종료"),
    ]

    def __init__(self, context: Context):
        super().__init__()
        self.context = context

    def on_mount(self) -> None:
        """메인 화면 마운트"""
        self.push_screen(MainScreen(self.context))
