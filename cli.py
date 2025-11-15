#!/usr/bin/env python3
# Textual 기반 주식 차트 뷰어

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Button, Label, ListView, ListItem, Input
from textual.screen import Screen
from textual import on, work
from textual_plotext import PlotextPlot
import pandas as pd
from modules.utils.fetch import fetch_time_series_daily
from datetime import datetime, timedelta
from pathlib import Path
import os


class ApiSettingsWidget(VerticalScroll):
    """API 키 설정 위젯"""

    def compose(self) -> ComposeResult:
        yield Static("API 설정", id="api-settings-title")
        with Horizontal(id="api-inputs-container"):
            with Vertical(id="google-api-section"):
                yield Static("Google API Key:", classes="api-label")
                yield Input(
                    placeholder="Google API 키를 입력하세요",
                    password=True,
                    id="google-api-input"
                )
            with Vertical(id="rapid-api-section"):
                yield Static("Rapid API Key:", classes="api-label")
                yield Input(
                    placeholder="Rapid API 키를 입력하세요",
                    password=True,
                    id="rapid-api-input"
                )
        with Horizontal(id="api-buttons-container"):
            yield Button("저장", id="save-api-button", variant="success")
            yield Button("초기화", id="clear-api-button", variant="error")
            yield Static("", id="api-status")

    def on_mount(self):
        """초기 환경변수 로드"""
        google_key = os.environ.get("GOOGLE_API_KEY", "")
        rapid_key = os.environ.get("RAPID_API_KEY", "")

        if google_key:
            self.query_one("#google-api-input", Input).value = google_key
        if rapid_key:
            self.query_one("#rapid-api-input", Input).value = rapid_key

        self.update_status()

    def update_status(self):
        """API 키 설정 상태 업데이트"""
        google_set = bool(os.environ.get("GOOGLE_API_KEY"))
        rapid_set = bool(os.environ.get("RAPID_API_KEY"))

        status = self.query_one("#api-status", Static)
        if google_set and rapid_set:
            status.update("✓ 모든 API 키 설정됨")
            status.styles.color = "green"
        elif google_set or rapid_set:
            status.update("⚠ 일부 API 키 설정됨")
            status.styles.color = "yellow"
        else:
            status.update("✗ API 키 미설정")
            status.styles.color = "red"

    def save_api_keys(self):
        """환경변수에 API 키 저장"""
        google_input = self.query_one("#google-api-input", Input)
        rapid_input = self.query_one("#rapid-api-input", Input)

        google_key = google_input.value.strip()
        rapid_key = rapid_input.value.strip()

        if google_key:
            os.environ["GOOGLE_API_KEY"] = google_key
        if rapid_key:
            os.environ["RAPID_API_KEY"] = rapid_key

        self.update_status()
        return google_key or rapid_key  # 하나라도 설정되었는지 확인

    def clear_api_keys(self):
        """환경변수에서 API 키 제거"""
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]
        if "RAPID_API_KEY" in os.environ:
            del os.environ["RAPID_API_KEY"]

        self.query_one("#google-api-input", Input).value = ""
        self.query_one("#rapid-api-input", Input).value = ""
        self.update_status()


class StockChart(Static):
    """주식 차트 위젯"""
    def __init__(self, ticker: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticker = ticker
        self.plt = PlotextPlot()
        self.data = None

    def compose(self) -> ComposeResult:
        yield self.plt

    def update_chart(self, data: pd.DataFrame) -> None:
        """차트 업데이트"""
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            plt = self.plt.plt
            plt.clear_data()
            plt.clear_figure()
            plt.title("No data available")
            self.plt.refresh()
            return

        plt = self.plt.plt
        plt.clear_data()
        plt.clear_figure()

        data = data.sort_values('timestamp')
        x_labels = data['timestamp'].dt.strftime('%Y-%m-%d').tolist()
        x = list(range(len(data)))
        y = data['close'].tolist()

        plt.plot(x, y, label="Close Price", marker="braille")
        plt.title(f"{self.ticker} - Daily Close Price")

        step = max(1, len(x_labels) // 10)
        plt.xticks([x[i] for i in range(0, len(x), step)],
                   [x_labels[i] for i in range(0, len(x_labels), step)])

        plt.xlabel("Date")
        plt.ylabel("Price ($)")
        self.plt.refresh()


class PortfolioWidget(Static):
    """포트폴리오 목록 위젯"""

    STOCK_LIST = ["AAPL", "GOOGL", "NVDA", "HPQ", "JPM"]

    def compose(self) -> ComposeResult:
        yield Static("포트폴리오 목록", id="portfolio-title")
        with VerticalScroll(id="portfolio-list"):
            for ticker in self.STOCK_LIST:
                yield Button(f"{ticker}", id=f"btn-{ticker}", classes="portfolio-item")


class AgentActivityWidget(Static):
    """에이전트 활동 위젯"""

    def get_activities_from_results(self):
        """results 폴더에서 활동 내역 가져오기"""
        activities = []
        results_path = Path("results")

        if not results_path.exists():
            return activities

        for ticker_dir in results_path.iterdir():
            if ticker_dir.is_dir():
                ticker = ticker_dir.name

                for date_dir in ticker_dir.iterdir():
                    if date_dir.is_dir():
                        date = date_dir.name
                        activities.append({"date": date, "ticker": ticker})

        activities.sort(key=lambda x: x["date"], reverse=True)
        return activities

    def compose(self) -> ComposeResult:
        yield Static("에이전트 활동", id="activity-title")
        with VerticalScroll(id="activity-log"):
            activities = self.get_activities_from_results()

            if activities:
                for activity in activities:
                    label = f"{activity['date']} {activity['ticker']}"
                    button_id = f"activity-{activity['ticker']}-{activity['date']}"
                    yield Button(label, id=button_id, classes="activity-item")
            else:
                yield Static("활동 내역이 없습니다.", classes="activity-item")

    def add_activity(self, message: str):
        """새로운 활동 로그 추가"""
        activity_log = self.query_one("#activity-log", VerticalScroll)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        activity_log.mount(Static(f"{timestamp}: {message}", classes="activity-item"))

    def refresh_activities(self):
        """활동 내역 새로고침"""
        activity_log = self.query_one("#activity-log", VerticalScroll)
        # 기존 항목 모두 제거
        activity_log.remove_children()

        # 새로운 활동 내역 추가
        activities = self.get_activities_from_results()
        if activities:
            for activity in activities:
                activity_log.mount(Static(activity, classes="activity-item"))
        else:
            activity_log.mount(Static("활동 내역이 없습니다.", classes="activity-item"))


class MainDashboard(Screen):
    """메인 대시보드 화면"""

    CSS = """
    MainDashboard {
        layout: vertical;
        background: $surface;
    }

    #api-settings-panel {
        height: 13;
        background: $boost;
        border: heavy $primary;
        padding: 1;
        margin: 0 0 1 0;
    }

    #api-settings {
        height: 100%;
        scrollbar-size: 1 1;
    }

    #api-settings-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        height: 1;
    }

    #api-inputs-container {
        layout: horizontal;
        height: auto;
    }

    #google-api-section, #rapid-api-section {
        width: 1fr;
        height: auto;
        padding: 0 1;
    }

    .api-label {
        color: $text;
        text-style: bold;
        height: 1;
    }

    #google-api-input, #rapid-api-input {
        width: 100%;
    }

    #api-buttons-container {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #api-buttons-container > Button {
        margin: 0 1;
        height: 3;
    }

    #api-status {
        margin-left: 2;
        text-style: bold;
        height: auto;
    }

    #main-content {
        layout: horizontal;
        height: 1fr;
        align: center middle;
    }

    #left-panel {
        width: 40%;
        height: 100%;
        background: $boost;
        border: heavy $primary;
        padding: 1;
    }

    #portfolio-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #portfolio-list {
        height: 1fr;
        border: solid $accent;
        padding: 1;
        background: $panel;
    }

    .portfolio-item {
        width: 100%;
        height: 3;
        margin: 0 0 1 0;
    }

    .portfolio-item:hover {
        background: $accent;
    }

    #center-panel {
        display: none;
    }

    #chart-area {
        height: 1fr;
    }

    #right-panel {
        width: 40%;
        height: 100%;
        background: $boost;
        border: heavy $primary;
        padding: 1;
        margin: 0 0 0 2;
    }

    #activity-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #activity-log {
        height: 1fr;
        border: solid $accent;
        padding: 1;
        background: $panel;
    }

    .activity-item {
        margin-bottom: 1;
        color: $text;
    }

    #chart-header {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.current_ticker = "AAPL"

    def compose(self) -> ComposeResult:
        yield Header()

        # API 설정 패널 (상단)
        with Container(id="api-settings-panel"):
            yield ApiSettingsWidget(id="api-settings")

        with Horizontal(id="main-content"):
            # 왼쪽 패널: 포트폴리오 목록 + 차트
            with Vertical(id="left-panel"):
                yield PortfolioWidget()
                yield Static("차트 화면", id="chart-header")
                with Container(id="chart-area"):
                    yield StockChart(ticker=self.current_ticker, id="stock-chart")

            # 오른쪽 패널: 에이전트 활동
            with Vertical(id="right-panel"):
                yield AgentActivityWidget(id="agent-activity")

        yield Footer()

    def on_mount(self):
        """화면 로드 시 초기 데이터 로드"""
        self.load_stock_data(self.current_ticker)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        """버튼 클릭 처리"""
        button_id = event.button.id

        # API 설정 버튼
        if button_id == "save-api-button":
            api_widget = self.query_one("#api-settings", ApiSettingsWidget)
            if api_widget.save_api_keys():
                self.notify("API 키가 환경변수에 저장되었습니다.", severity="information")
            else:
                self.notify("저장할 API 키를 입력하세요.", severity="warning")

        elif button_id == "clear-api-button":
            api_widget = self.query_one("#api-settings", ApiSettingsWidget)
            api_widget.clear_api_keys()
            self.notify("API 키가 초기화되었습니다.", severity="information")

        # 포트폴리오 버튼 클릭
        elif button_id and button_id.startswith("btn-"):
            ticker = button_id.replace("btn-", "")
            # StockChartScreen으로 전환
            self.app.push_screen(StockChartScreen(ticker))

        # 활동 내역 버튼 클릭
        elif button_id and button_id.startswith("activity-"):
            # activity-{ticker}-{date} 형식 파싱
            parts = button_id.replace("activity-", "").split("-")
            if len(parts) >= 2:
                ticker = parts[0]
                date = "-".join(parts[1:])  # 날짜에 '-'가 포함되어 있으므로
                # ReportScreen으로 전환
                self.app.push_screen(ReportScreen(ticker, date))

    @work(exclusive=True)
    async def load_stock_data(self, ticker: str):
        """주식 데이터 로드"""
        try:
            self.notify(f"{ticker} 데이터 로딩 중...", severity="information")

            # 최근 30일간의 데이터 가져오기
            to_date = datetime.now()
            from_date = to_date - timedelta(days=30)

            from_date_str = from_date.strftime("%Y%m%d")
            to_date_str = to_date.strftime("%Y%m%d")

            data = fetch_time_series_daily(ticker=ticker, date_from=from_date_str, date_to=to_date_str)

            if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                self.notify(f"{ticker} 데이터가 비어있습니다. API 키를 확인하세요.", severity="warning")
            else:
                self.notify(f"{ticker} 데이터 로드 완료: {len(data)}개 행", severity="information")

            chart = self.query_one("#stock-chart", StockChart)
            chart.ticker = ticker
            chart.update_chart(data)

        except Exception as e:
            self.notify(f"데이터 로딩 에러: {str(e)}", severity="error")


class ReportScreen(Screen):
    """보고서 목록 화면"""

    CSS = """
    ReportScreen {
        layout: vertical;
        background: $surface;
    }

    #report-header {
        height: auto;
        background: $boost;
        padding: 1;
        text-align: center;
    }

    #report-title {
        text-style: bold;
        color: $accent;
    }

    #report-list-container {
        height: 1fr;
        border: heavy $accent;
        background: $panel;
        padding: 2;
        margin: 1;
    }

    .report-item {
        width: 100%;
        height: 3;
        margin: 0 0 1 0;
    }

    .report-item:hover {
        background: $accent;
    }

    #button-container {
        height: auto;
        layout: horizontal;
        padding: 1;
        align: center middle;
    }

    #button-container > Button {
        margin: 0 2;
    }

    Button:hover {
        background: $accent;
    }
    """

    BINDINGS = [
        ("escape", "back", "Back"),
    ]

    def __init__(self, ticker: str, date: str):
        super().__init__()
        self.ticker = ticker
        self.date = date

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="report-header"):
            yield Static(f"{self.ticker} - {self.date} 보고서 목록", id="report-title")

        with VerticalScroll(id="report-list-container"):
            yield Static("사용 가능한 보고서:", id="report-list-title")
            for report_info in self.get_available_reports():
                file_id = report_info['filename'].replace('.', '_')
                yield Button(
                    report_info["display_name"],
                    id=f"report-{file_id}",
                    classes="report-item"
                )

        with Container(id="button-container"):
            yield Button("← Back", id="back-button", variant="warning")

        yield Footer()

    def get_available_reports(self):
        """사용 가능한 보고서 목록 가져오기"""
        report_path = Path(f"results/{self.ticker}/{self.date}/reports/")
        reports = []

        if not report_path.exists():
            return reports

        report_files = {
            "market_report.md": "시장 분석 보고서",
            "investment_plan.md": "투자 계획",
        }

        for filename, display_name in report_files.items():
            file_path = report_path / filename
            if file_path.exists():
                reports.append({
                    "filename": filename,
                    "display_name": display_name,
                    "path": str(file_path)
                })

        return reports

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        """버튼 클릭 처리"""
        button_id = event.button.id

        if button_id == "back-button":
            self.app.pop_screen()
        elif button_id and button_id.startswith("report-"):
            # ID에서 파일명을 복원 (언더스코어를 점으로 변경)
            file_id = button_id.replace("report-", "")
            filename = file_id.replace('_', '.')
            self.app.push_screen(ReportDetailScreen(self.ticker, self.date, filename))

    def action_back(self):
        """ESC 키로 돌아가기"""
        self.app.pop_screen()


class ReportDetailScreen(Screen):
    """보고서 상세 화면"""

    CSS = """
    ReportDetailScreen {
        layout: vertical;
        background: $surface;
    }

    #detail-header {
        height: auto;
        background: $boost;
        padding: 1;
        text-align: center;
    }

    #detail-title {
        text-style: bold;
        color: $accent;
    }

    #detail-content {
        height: 1fr;
        border: heavy $accent;
        background: $panel;
        padding: 2;
        margin: 1;
    }

    #button-container {
        height: auto;
        layout: horizontal;
        padding: 1;
        align: center middle;
    }

    #button-container > Button {
        margin: 0 2;
    }

    Button:hover {
        background: $accent;
    }
    """

    BINDINGS = [
        ("escape", "back", "Back"),
    ]

    def __init__(self, ticker: str, date: str, filename: str):
        super().__init__()
        self.ticker = ticker
        self.date = date
        self.filename = filename

    def compose(self) -> ComposeResult:
        yield Header()

        # 파일명에 따른 표시 이름
        display_names = {
            "market_report.md": "시장 분석 보고서",
            "investment_plan.md": "투자 계획",
        }

        display_name = display_names.get(self.filename, self.filename)

        with Container(id="detail-header"):
            yield Static(f"{self.ticker} - {self.date} | {display_name}", id="detail-title")

        with VerticalScroll(id="detail-content"):
            yield Static(self.load_report_content(), id="detail-text")

        with Container(id="button-container"):
            yield Button("← Back", id="back-button", variant="warning")

        yield Footer()

    def load_report_content(self) -> str:
        """보고서 내용 로드"""
        report_path = Path(f"results/{self.ticker}/{self.date}/reports/{self.filename}")

        if not report_path.exists():
            return "보고서를 찾을 수 없습니다."

        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"보고서를 읽는 중 오류가 발생했습니다: {str(e)}"

    @on(Button.Pressed, "#back-button")
    def go_back(self):
        """목록으로 돌아가기"""
        self.app.pop_screen()

    def action_back(self):
        """ESC 키로 돌아가기"""
        self.app.pop_screen()


class StockChartScreen(Screen):

    CSS = """
    StockChartScreen {
        layout: vertical;
        background: $surface;
    }

    #chart-header {
        height: auto;
        background: $boost;
        padding: 1;
        text-align: center;
    }

    #chart-title {
        text-style: bold;
        color: $accent;
    }

    #chart-main {
        height: 1fr;
        border: heavy $accent;
        background: $panel;
        padding: 1;
        margin: 1;
    }

    #button-container {
        height: auto;
        layout: horizontal;
        padding: 1;
        align: center middle;
    }

    #button-container > Button {
        margin: 0 2;
    }

    Button:hover {
        background: $accent;
    }
    """

    BINDINGS = [
        ("escape", "back", "Back"),
    ]

    def __init__(self, ticker: str):
        super().__init__()
        self.ticker = ticker

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="chart-header"):
            yield Static(f" {self.ticker} Stock Chart", id="chart-title")

        with Container(id="chart-main"):
            yield StockChart(ticker=self.ticker, id="stock-chart")

        with Container(id="button-container"):
            yield Button("← Back to List", id="back-button", variant="warning")

        yield Footer()

    def on_mount(self):
        """화면이 로드되면 주식 데이터를 가져옴"""
        self.load_stock_data()

    @work(exclusive=True)
    async def load_stock_data(self):
        """주식 데이터 로드"""
        try:
            self.notify(f"{self.ticker} 데이터 로딩 중...", severity="information")

            # 최근 30일간의 데이터 가져오기
            to_date = datetime.now()
            from_date = to_date - timedelta(days=30)

            from_date_str = from_date.strftime("%Y%m%d")
            to_date_str = to_date.strftime("%Y%m%d")

            data = fetch_time_series_daily(ticker=self.ticker, date_from=from_date_str, date_to=to_date_str)

            if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                self.notify(f"{self.ticker} 데이터가 비어있습니다. API 키를 확인하세요.", severity="warning")
            else:
                self.notify(f"{self.ticker} 데이터 로드 완료: {len(data)}개 행", severity="information")

            chart = self.query_one("#stock-chart", StockChart)
            chart.update_chart(data)

        except Exception as e:
            self.notify(f"데이터 로딩 에러: {str(e)}", severity="error")

    @on(Button.Pressed, "#back-button")
    def go_back(self):
        """목록으로 돌아가기"""
        self.app.pop_screen()

    def action_back(self):
        """ESC 키로 돌아가기"""
        self.app.pop_screen()


class StockViewerApp(App):
    """메인 애플리케이션"""

    TITLE = "Multi-Trading Agents Dashboard"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def on_mount(self):
        """앱 시작 시 메인 대시보드 화면 표시"""
        self.push_screen(MainDashboard())


def main():
    app = StockViewerApp()
    app.run()


if __name__ == "__main__":
    main()
