"""접기/펼치기 가능한 보고서 컴포넌트"""

from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import Container, VerticalScroll


class ReportToggle(Container):
    """접기/펼치기 가능한 보고서 위젯"""

    def __init__(self, title: str, content: str, report_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.content = content
        self.report_type = report_type
        self.is_expanded = False
        self.content_widget: Static | None = None
        self.add_class("report-toggle-container")

    def compose(self) -> ComposeResult:
        yield Button(f"> {self.title}", id=f"toggle-{self.report_type}", classes="report-toggle-button")
        yield Container(id=f"content-{self.report_type}", classes="content-wrapper")

    async def toggle(self) -> None:
        """보고서 펼치기/접기 토글"""
        self.is_expanded = not self.is_expanded
        button = self.query_one(f"#toggle-{self.report_type}", Button)
        content_wrapper = self.query_one(f"#content-{self.report_type}", Container)

        if self.is_expanded:
            button.label = f"v {self.title}"
            self.content_widget = Static(self.content, classes="report-content")
            await content_wrapper.mount(VerticalScroll(self.content_widget, classes="report-content-container"))
        else:
            button.label = f"> {self.title}"
            await content_wrapper.remove_children()
            self.content_widget = None

    def set_content(self, content: str) -> None:
        """보고서 내용 업데이트"""
        self.content = content
        if self.is_expanded and self.content_widget:
            self.content_widget.update(content)
