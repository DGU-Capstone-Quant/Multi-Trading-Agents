"""CLI 내에서 컨텍스트 변경을 알리기 위한 메시지 정의"""
from textual.message import Message


class ContextUpdated(Message):
    """컨텍스트 변경을 구독 위젯에 알리는 메시지"""

    def __init__(self) -> None:
        super().__init__()
