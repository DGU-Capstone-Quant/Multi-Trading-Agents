"""CLI 기본 클래스"""

from textual.screen import Screen
from textual.widgets import Static
from textual.app import ComposeResult
from modules.context import Context


class BaseScreen(Screen):
    """화면 기본 클래스"""

    def __init__(self, context: Context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = context

    def compose(self) -> ComposeResult:
        raise NotImplementedError("compose 메서드를 구현해야 합니다")


class BaseWidget(Static):
    """위젯 기본 클래스"""

    def __init__(self, context: Context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = context

    def compose(self) -> ComposeResult:
        raise NotImplementedError("compose 메서드를 구현해야 합니다")

    async def refresh_data(self) -> None:
        raise NotImplementedError("refresh_data 메서드를 구현해야 합니다")
