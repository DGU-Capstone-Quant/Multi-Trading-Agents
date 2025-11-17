"""CLI 기본 클래스 모듈"""

from textual.screen import Screen
from textual.widgets import Static
from textual.app import ComposeResult
from modules.context import Context


class BaseScreen(Screen):
    """모든 Screen의 기본 클래스"""

    def __init__(self, context: Context, *args, **kwargs):
        """
        Args:
            context: Context 객체
        """
        super().__init__(*args, **kwargs)
        self.context = context

    def compose(self) -> ComposeResult:
        """화면 구성"""
        raise NotImplementedError("compose 메서드를 구현해야 합니다")


class BaseWidget(Static):
    """모든 Widget의 기본 클래스"""

    def __init__(self, context: Context, *args, **kwargs):
        """
        Args:
            context: Context 객체
        """
        super().__init__(*args, **kwargs)
        self.context = context

    def compose(self) -> ComposeResult:
        """위젯 구성"""
        raise NotImplementedError("compose 메서드를 구현해야 합니다")

    async def refresh_data(self) -> None:
        """데이터 새로고침"""
        raise NotImplementedError("refresh_data 메서드를 구현해야 합니다")
