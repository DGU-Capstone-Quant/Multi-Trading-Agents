"""트레이딩 대시보드 메인 애플리케이션"""

from typing import Dict, List
from textual.app import App

from modules.context import Context
from cli.screens import MainScreen


class TradingDashboardApp(App):
    """멀티 트레이딩 에이전트 대시보드 애플리케이션"""

    TITLE = "멀티 트레이딩 에이전트 대시보드"

    BINDINGS = [
        ("q", "quit", "종료"),
    ]

    def __init__(self, context: Context, date_ticker_map: Dict[str, List[str]]):
        super().__init__()
        self.context = context
        self.date_ticker_map = date_ticker_map

    def on_mount(self) -> None:
        """앱 시작 시 메인 화면 마운트"""
        self.push_screen(MainScreen(self.context, self.date_ticker_map))
