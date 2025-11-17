"""트레이딩 대시보드 화면 모듈"""

import os
import pandas as pd
import plotext as plt
from abc import ABC
from typing import Optional
from datetime import datetime, timedelta
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, Label, LoadingIndicator
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on, work
from textual.message import Message
from textual_plotext import PlotextPlot

from modules.context import Context
from modules.utils.fetch import fetch_time_series_daily
from cli.base import BaseScreen
from cli.manager import DebateManager
from cli.widgets import PortfolioWidget, ActivityWidget


# ============================================================================
# Main Screen
# ============================================================================

class MainScreen(BaseScreen):
    """포트폴리오와 완료된 토론이 있는 메인 대시보드 화면"""

    class DebateCompleted(Message):
        """토론 완료 메시지"""
        def __init__(self, ticker: str, trade_date: str) -> None:
            super().__init__()
            self.ticker = ticker
            self.trade_date = trade_date

    class AllDebatesCompleted(Message):
        """모든 토론 완료 메시지"""
        def __init__(self, trade_date: str, completed: list, failed: list) -> None:
            super().__init__()
            self.trade_date = trade_date
            self.completed = completed
            self.failed = failed

    CSS = """
    MainScreen {
        layout: vertical;
        background: $surface;
    }

    #top-section {
        height: 7;
        layout: vertical;
        margin-bottom: 1;
        background: $boost;
        border: heavy $primary;
        padding: 1;
    }

    #api-keys-container {
        layout: horizontal;
        height: auto;
    }

    .api-key-group {
        layout: horizontal;
        width: 1fr;
        height: auto;
        align: left middle;
        margin-right: 2;
    }

    .api-key-group:last-child {
        margin-right: 0;
    }

    .api-key-label {
        width: 12;
        content-align: right middle;
        color: $accent;
        text-style: bold;
        padding-right: 1;
    }

    .api-key-input {
        width: 1fr;
        height: auto;
    }

    .api-key-status {
        width: 2;
        content-align: center middle;
        text-align: center;
        margin-left: 1;
    }

    #control-bar {
        layout: horizontal;
        height: 7;
        background: $panel;
        border: solid $secondary;
        padding: 1 2;
        align: center middle;
    }

    #timer-info {
        width: 1fr;
        height: 5;
        color: $text;
        text-style: bold;
        content-align: left middle;
        padding: 1;
    }

    #manual-debate-btn {
        width: auto;
        height: 5;
        min-width: 15;
        padding: 1 2;
        margin-left: 2;
    }

    #manual-debate-btn:hover {
        background: $warning;
    }

    #main-content {
        layout: horizontal;
        height: 1fr;
    }

    #left-panel {
        width: 50%;
        height: 100%;
        background: $boost;
        border: heavy $primary;
        padding: 1;
        margin-right: 1;
    }

    #right-panel {
        width: 50%;
        height: 100%;
        background: $boost;
        border: heavy $primary;
        padding: 1;
    }

    .portfolio-item {
        width: 100%;
        height: 3;
        margin: 0 0 1 0;
    }

    .portfolio-item:hover {
        background: $accent;
    }

    .activity-item {
        width: 100%;
        height: 3;
        margin: 0 0 1 0;
    }

    .activity-item:hover {
        background: $accent;
    }

    #status-text {
        color: $text;
    }
    """

    BINDINGS = [
        ("q", "quit", "종료"),
        ("r", "refresh", "새로고침"),
        ("d", "debate", "토론 실행"),
    ]

    def __init__(self, context: Context, date_ticker_map: dict):
        """
        Args:
            context: Context 객체
            date_ticker_map: 날짜별 종목 매핑
        """
        super().__init__(context)

        # Debate Manager
        self.debate_manager = DebateManager(context, date_ticker_map)

        # API 키
        self.rapid_api_key = os.getenv("RAPID_API_KEY", "")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")

        # 타이머 (1분 = 60초)
        self.time_remaining = 60
        self.total_interval = 60

    def compose(self) -> ComposeResult:
        yield Header()

        # 상단 섹션
        with Container(id="top-section"):
            with Horizontal(id="api-keys-container"):
                # RAPID API KEY
                with Horizontal(classes="api-key-group"):
                    yield Label("RAPID API:", classes="api-key-label")
                    yield Input(
                        placeholder="API Key",
                        password=True,
                        value=self.rapid_api_key,
                        id="rapid-api-key-input",
                        classes="api-key-input"
                    )
                    yield Static(
                        "✓" if self.rapid_api_key else "✗",
                        id="rapid-api-key-status",
                        classes="api-key-status"
                    )

                # GOOGLE API KEY
                with Horizontal(classes="api-key-group"):
                    yield Label("GOOGLE API:", classes="api-key-label")
                    yield Input(
                        placeholder="API Key",
                        password=True,
                        value=self.google_api_key,
                        id="google-api-key-input",
                        classes="api-key-input"
                    )
                    yield Static(
                        "✓" if self.google_api_key else "✗",
                        id="google-api-key-status",
                        classes="api-key-status"
                    )

        # 메인 컨텐츠
        with Horizontal(id="main-content"):
            # 왼쪽 패널: 포트폴리오
            with Vertical(id="left-panel"):
                yield PortfolioWidget(self.context, id="portfolio-widget")

            # 오른쪽 패널: 활동 내역
            with Vertical(id="right-panel"):
                yield ActivityWidget(self.context, id="activity-widget")

        # 컨트롤 바
        with Horizontal(id="control-bar"):
            yield Static(f"⏱️ 다음 자동 거래: {self._format_time(self.time_remaining)}", id="timer-info")
            yield Button("▶ 거래실행", id="manual-debate-btn", variant="success")

        yield Footer()

    def on_mount(self) -> None:
        """화면 마운트 시 초기화"""
        self.set_interval(1, self.update_timer)
        self.set_interval(60, self.on_auto_refresh)

    @on(Input.Changed, "#rapid-api-key-input")
    def on_rapid_api_key_changed(self, event: Input.Changed) -> None:
        """RAPID API 키 입력 변경 처리"""
        self.rapid_api_key = event.value
        os.environ["RAPID_API_KEY"] = self.rapid_api_key

        status = self.query_one("#rapid-api-key-status", Static)
        if self.rapid_api_key:
            status.update("✓")
            status.styles.color = "green"
        else:
            status.update("✗")
            status.styles.color = "red"

        self.update_status(f"RAPID API 키 {'설정됨' if self.rapid_api_key else '제거됨'}")

    @on(Input.Changed, "#google-api-key-input")
    def on_google_api_key_changed(self, event: Input.Changed) -> None:
        """GOOGLE API 키 입력 변경 처리"""
        self.google_api_key = event.value
        os.environ["GOOGLE_API_KEY"] = self.google_api_key

        status = self.query_one("#google-api-key-status", Static)
        if self.google_api_key:
            status.update("✓")
            status.styles.color = "green"
        else:
            status.update("✗")
            status.styles.color = "red"

        self.update_status(f"GOOGLE API 키 {'설정됨' if self.google_api_key else '제거됨'}")

    def update_timer(self) -> None:
        """타이머 업데이트 (1초마다 호출)"""
        self.time_remaining -= 1

        if self.time_remaining <= 0:
            self.time_remaining = self.total_interval

        try:
            timer_info = self.query_one("#timer-info", Static)
            timer_info.update(f"⏱️ 다음 자동 거래: {self._format_time(self.time_remaining)}")
        except:
            pass

    def _format_time(self, seconds: int) -> str:
        """초를 시:분:초 형식으로 변환"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def _get_progress_bar(self) -> str:
        """진행률 바 생성"""
        if self.total_interval == 0:
            return ""

        progress = self.time_remaining / self.total_interval
        filled = int((1 - progress) * 30)
        empty = 30 - filled

        return f"[{'█' * filled}{'░' * empty}] {int((1 - progress) * 100)}%"

    def on_auto_refresh(self) -> None:
        """자동 토론 실행 (1분마다)"""
        self.time_remaining = self.total_interval
        self.run_auto_debate()

    def run_auto_debate(self) -> None:
        """자동 토론 실행 (날짜별 모든 종목 처리)"""
        if not self.rapid_api_key:
            self.update_status("❌ RAPID API 키가 설정되지 않았습니다")
            self.notify("RAPID API 키를 먼저 입력해주세요", severity="error")
            return

        if not self.google_api_key:
            self.update_status("❌ GOOGLE API 키가 설정되지 않았습니다")
            self.notify("GOOGLE API 키를 먼저 입력해주세요", severity="error")
            return

        items = self.debate_manager.get_next_debate_items()

        if not items:
            self.update_status("⚠️ 토론할 항목이 없습니다")
            self.notify("날짜별 종목 데이터가 없습니다", severity="warning")
            return

        trade_date = items[0]["trade_date"]
        tickers = [item["ticker"] for item in items]

        self.update_status(f"🎯 토론 시작: {trade_date} - {len(tickers)}개 종목 ({', '.join(tickers)})")
        self.notify(f"토론 시작: {trade_date} - {len(tickers)}개 종목", severity="information")

        import threading

        def run_debate_thread():
            """날짜별 모든 종목 토론 실행"""
            completed = []
            failed = []

            for item in items:
                ticker = item["ticker"]
                trade_date_item = item["trade_date"]

                try:
                    success = self.debate_manager.run_debate(ticker, trade_date_item)

                    if success:
                        completed.append(ticker)
                        self.post_message(self.DebateCompleted(ticker, trade_date_item))
                    else:
                        failed.append(ticker)

                except Exception:
                    failed.append(ticker)

            self.post_message(self.AllDebatesCompleted(trade_date, completed, failed))

        thread = threading.Thread(target=run_debate_thread, daemon=True)
        thread.start()

    @on(DebateCompleted)
    async def handle_debate_completed(self, message: DebateCompleted) -> None:
        """개별 토론 완료 메시지 핸들러"""
        try:
            activity_widget = self.query_one("#activity-widget", ActivityWidget)
            await activity_widget.refresh_data()
            self.update_status(f"✅ 토론 완료: {message.ticker} ({message.trade_date})")
        except Exception:
            pass

    @on(AllDebatesCompleted)
    async def handle_all_debates_completed(self, message: AllDebatesCompleted) -> None:
        """모든 토론 완료 메시지 핸들러"""
        total = len(message.completed) + len(message.failed)

        if message.failed:
            self.update_status(
                f"⚠️ 토론 완료: {message.trade_date} - 성공 {len(message.completed)}/{total}, 실패 {len(message.failed)}/{total}"
            )
            self.notify(
                f"토론 완료: {message.trade_date}\n성공: {', '.join(message.completed)}\n실패: {', '.join(message.failed)}",
                severity="warning"
            )
        else:
            self.update_status(f"✅ 토론 완료: {message.trade_date} - {len(message.completed)}개 종목 모두 성공")
            self.notify(f"토론 완료: {message.trade_date} - {', '.join(message.completed)}", severity="information")

        await self.refresh_data()

    async def refresh_data(self) -> None:
        """모든 데이터 새로고침"""
        portfolio_widget = self.query_one("#portfolio-widget", PortfolioWidget)
        await portfolio_widget.refresh_data()

        activity_widget = self.query_one("#activity-widget", ActivityWidget)
        await activity_widget.refresh_data()

        self.update_status("데이터 새로고침 완료")

    def update_status(self, message: str) -> None:
        """상태 메시지 표시"""
        _ = message

    @on(Button.Pressed, "#manual-debate-btn")
    def on_manual_debate_pressed(self) -> None:
        """수동 토론 버튼 클릭"""
        self.action_debate()

    def action_debate(self) -> None:
        """수동 토론 실행 액션"""
        self.run_auto_debate()
        self.time_remaining = self.total_interval

    async def action_refresh(self) -> None:
        """수동 새로고침 액션"""
        await self.refresh_data()
        self.notify("데이터 새로고침 완료", severity="information")

    def action_quit(self) -> None:
        """종료 액션"""
        self.app.exit()


# ============================================================================
# Debate Detail Screen
# ============================================================================

class ReportToggle(Container):
    """토글 가능한 보고서 위젯"""

    def __init__(self, title: str, content: str, report_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.content = content
        self.report_type = report_type
        self.is_expanded = False
        self.add_class("report-toggle-container")

    def compose(self) -> ComposeResult:
        """위젯 구성"""
        yield Button(
            f"▶  {self.title}  (클릭하여 펼치기)",
            id=f"toggle-{self.report_type}",
            classes="report-toggle-button"
        )
        yield Container(id=f"content-{self.report_type}", classes="content-wrapper")

    def _format_content(self, content: str) -> str:
        """보고서 내용을 읽기 쉽게 포맷팅"""
        lines = content.split('\n')
        formatted_lines = []

        for i, line in enumerate(lines):
            if line.strip().startswith('#') or line.strip().startswith('---') or line.strip().startswith('==='):
                if i > 0 and formatted_lines and formatted_lines[-1].strip():
                    formatted_lines.append('')
                formatted_lines.append(line)
                if i < len(lines) - 1:
                    formatted_lines.append('')
            else:
                formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    async def toggle(self) -> None:
        """보고서 내용 펼치기/접기"""
        self.is_expanded = not self.is_expanded

        button = self.query_one(f"#toggle-{self.report_type}", Button)
        content_wrapper = self.query_one(f"#content-{self.report_type}", Container)

        if self.is_expanded:
            button.label = f"▼  {self.title}  (클릭하여 접기)"
            await content_wrapper.mount(
                VerticalScroll(
                    Static(self._format_content(self.content), classes="report-content"),
                    classes="report-content-container"
                )
            )
        else:
            button.label = f"▶  {self.title}  (클릭하여 펼치기)"
            await content_wrapper.remove_children()


class DebateDetailScreen(BaseScreen):
    """토론 상세 화면"""

    CSS = """
    DebateDetailScreen {
        layout: vertical;
        background: $surface;
    }

    #detail-container {
        layout: vertical;
        height: 1fr;
        padding: 1 2;
    }

    #detail-header {
        height: auto;
        background: $boost;
        border: heavy $primary;
        padding: 1 2;
        margin-bottom: 1;
    }

    #detail-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }

    #detail-info {
        color: $text;
        text-align: center;
        text-style: bold;
    }

    #reports-container {
        layout: vertical;
        height: 1fr;
        overflow-y: auto;
        padding: 0 1;
    }

    .report-toggle-container {
        layout: vertical;
        height: auto;
        background: $panel;
        border: heavy $primary;
        padding: 0;
        margin-bottom: 2;
        overflow: hidden;
    }

    .report-toggle-button {
        width: 100%;
        height: 3;
        background: $boost;
        color: $accent;
        text-align: left;
        text-style: bold;
        border: none;
        padding: 0 2;
    }

    .report-toggle-button:hover {
        background: $primary;
        color: $text;
    }

    .report-toggle-button:focus {
        background: $primary;
    }

    .content-wrapper {
        height: auto;
        width: 100%;
    }

    .report-content-container {
        height: 40;
        max-height: 40;
        margin: 0;
        padding: 2;
        background: $surface;
        border-top: solid $secondary;
        overflow-x: auto;
        overflow-y: auto;
    }

    .report-content {
        color: $text;
        padding: 1;
        background: $surface;
        border: none;
        width: 100%;
        content-align: left top;
    }

    #back-button {
        width: 25;
        height: 3;
        margin: 1 0;
        background: $warning;
        text-style: bold;
    }

    #back-button:hover {
        background: $error;
        color: $text;
    }
    """

    BINDINGS = [
        ("escape", "back", "뒤로 가기"),
    ]

    def __init__(self, context: Context, ticker: str, trade_date: str, *args, **kwargs):
        """
        Args:
            context: Context 객체
            ticker: 종목 코드
            trade_date: 거래 날짜
        """
        super().__init__(context, *args, **kwargs)
        self.ticker = ticker
        self.trade_date = trade_date

    def compose(self) -> ComposeResult:
        """화면 구성"""
        yield Header()

        with Container(id="detail-container"):
            # 헤더 정보
            with Container(id="detail-header"):
                yield Static(
                    f"토론 상세 보고서",
                    id="detail-title"
                )
                yield Static(
                    f"Ticker: {self.ticker} | Trade Date: {self.trade_date}",
                    id="detail-info"
                )

            # 보고서 목록
            with VerticalScroll(id="reports-container"):
                # market_report
                market_report = self._get_report("market_report")
                if market_report:
                    yield ReportToggle(
                        "📊 Market Report (마켓 리포트)",
                        market_report,
                        "market_report"
                    )

                # investment_plan
                investment_plan = self._get_report("investment_plan")
                if investment_plan:
                    yield ReportToggle(
                        "📈 Investment Plan (투자 계획)",
                        investment_plan,
                        "investment_plan"
                    )

                # trader_decision
                trader_decision = self._get_report("trader_decision")
                if trader_decision:
                    yield ReportToggle(
                        "💼 Trader Decision (트레이더 결정)",
                        trader_decision,
                        "trader_decision"
                    )

            # 뒤로 가기 버튼
            yield Button("← 뒤로 가기", id="back-button", variant="warning")

        yield Footer()

    def _get_report(self, report_type: str) -> str:
        """
        Context에서 보고서 가져오기

        Args:
            report_type: market_report, investment_plan, trader_decision

        Returns:
            보고서 내용 또는 빈 문자열
        """
        if report_type == "investment_plan":
            key = f"{self.ticker}_{self.trade_date}_investment_plan"
            content = self.context.get_report(key)
            if not content:
                return f"투자 계획 보고서를 찾을 수 없습니다.\n(키: {key})"
            return content

        if report_type == "trader_decision":
            decision_key = f"{self.ticker}_{self.trade_date}_trader_decision"
            recommendation_key = f"{self.ticker}_{self.trade_date}_trader_recommendation"

            decision = self.context.get_cache(decision_key, "")
            recommendation = self.context.get_cache(recommendation_key, "")

            if not decision and not recommendation:
                return f"트레이더 결정 보고서를 찾을 수 없습니다.\n(키: {decision_key}, {recommendation_key})"

            content = f"**Decision:**\n{decision}\n\n**Recommendation:**\n{recommendation}"
            return content

        key = f"{self.ticker}_{self.trade_date}_{report_type}"
        content = self.context.get_report(key)

        if not content:
            return f"[{report_type}] 보고서를 찾을 수 없습니다.\n(키: {key})"

        return content

    @on(Button.Pressed, ".report-toggle-button")
    async def on_toggle_button_pressed(self, event: Button.Pressed) -> None:
        """토글 버튼 클릭 처리"""
        toggle_widget = event.button.parent
        if isinstance(toggle_widget, ReportToggle):
            await toggle_widget.toggle()

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        """뒤로 가기 버튼 클릭"""
        self.action_back()

    def action_back(self) -> None:
        """뒤로 가기 액션"""
        self.app.pop_screen()


# ============================================================================
# Stock Chart Screen
# ============================================================================

class StockChartScreen(BaseScreen):
    """주가 차트 화면"""

    CSS = """
    StockChartScreen {
        layout: vertical;
        background: $surface;
    }

    #chart-container {
        layout: vertical;
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }

    #chart-header {
        height: auto;
        background: $boost;
        border: heavy $primary;
        padding: 1 2;
        margin-bottom: 1;
    }

    #chart-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }

    #chart-info {
        color: $text;
        text-align: center;
    }

    #chart-content {
        layout: vertical;
        height: auto;
        min-height: 25;
        background: $panel;
        border: heavy $primary;
        padding: 0;
        margin-bottom: 1;
    }

    PlotextPlot {
        height: 25;
        width: 100%;
    }

    #price-table {
        height: auto;
        background: $surface;
        border: solid $secondary;
        padding: 1 2;
        margin-top: 1;
    }

    .chart-text {
        color: $text;
        background: $surface;
    }

    .loading {
        text-align: center;
        color: $warning;
        text-style: bold;
    }

    .error {
        text-align: center;
        color: $error;
        text-style: bold;
    }

    #button-container {
        layout: horizontal;
        height: auto;
        padding: 0 2;
    }

    #back-button {
        width: 25;
        height: 3;
        margin: 1 1;
        background: $warning;
        text-style: bold;
    }

    #back-button:hover {
        background: $error;
        color: $text;
    }

    #refresh-button {
        width: 25;
        height: 3;
        margin: 1 1;
        background: $primary;
        text-style: bold;
    }

    #refresh-button:hover {
        background: $accent;
        color: $text;
    }
    """

    BINDINGS = [
        ("escape", "back", "뒤로 가기"),
        ("r", "refresh", "새로고침"),
    ]

    def __init__(self, context: Context, ticker: str, *args, **kwargs):
        """
        Args:
            context: Context 객체
            ticker: 종목 코드
        """
        super().__init__(context, *args, **kwargs)
        self.ticker = ticker
        self.df = None

    def compose(self) -> ComposeResult:
        """화면 구성"""
        yield Header()

        with Container(id="chart-container"):
            # 헤더 정보
            with Container(id="chart-header"):
                yield Static(
                    f"📈 주가 차트",
                    id="chart-title"
                )
                yield Static(
                    f"Ticker: {self.ticker}",
                    id="chart-info"
                )

            # 차트 내용
            with Container(id="chart-content"):
                yield PlotextPlot(id="chart-plot")

            # 가격 테이블
            with VerticalScroll(id="price-table"):
                yield Static("", id="price-data")

            # 버튼 컨테이너
            with Horizontal(id="button-container"):
                yield Button("← 뒤로 가기", id="back-button", variant="warning")
                yield Button("🔄 새로고침", id="refresh-button", variant="primary")

        yield Footer()

    async def on_mount(self) -> None:
        """마운트 시 데이터 로드"""
        await self.load_stock_data()

    async def load_stock_data(self) -> None:
        """주가 데이터 로드"""
        try:
            # 최근 6개월 데이터 가져오기
            date_to = datetime.now().strftime("%Y-%m-%d")
            date_from = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

            # API에서 데이터 가져오기
            self.df = fetch_time_series_daily(
                ticker=self.ticker,
                date_from=date_from,
                date_to=date_to
            )

            if self.df is None or self.df.empty:
                chart_plot = self.query_one("#chart-plot", PlotextPlot)
                chart_plot.plt.clear_data()
                chart_plot.plt.clear_figure()
                chart_plot.plt.title(f"No data available for {self.ticker}")
                chart_plot.refresh()
                return

            # UI 업데이트
            self.display_chart()

        except Exception as e:
            chart_plot = self.query_one("#chart-plot", PlotextPlot)
            chart_plot.plt.clear_data()
            chart_plot.plt.clear_figure()
            chart_plot.plt.title(f"Error: {str(e)}")
            chart_plot.refresh()

    def display_chart(self) -> None:
        """차트 표시"""
        if self.df is None or self.df.empty:
            return

        chart_plot = self.query_one("#chart-plot", PlotextPlot)
        price_data = self.query_one("#price-data", Static)

        # 최근 60일 데이터만 사용
        df_chart = self.df.head(60).copy()
        df_chart = df_chart.sort_values('timestamp')

        # 날짜와 가격 데이터 준비
        dates = df_chart['timestamp'].dt.strftime('%Y-%m-%d').tolist()
        close_prices = df_chart['close'].tolist()

        # X축은 숫자 인덱스 사용
        x = list(range(len(df_chart)))

        # plotext 직접 사용
        plt_obj = chart_plot.plt
        plt_obj.clear_data()
        plt_obj.clear_figure()

        # 종가 라인 차트
        plt_obj.plot(x, close_prices, label="Close", marker="braille")

        # 차트 설정
        plt_obj.title(f"{self.ticker} Stock Price (Last 60 Days)")
        plt_obj.xlabel("Date")
        plt_obj.ylabel("Price ($)")

        # X축 레이블 간격 조정
        step = max(1, len(x) // 10)
        plt_obj.xticks(
            [x[i] for i in range(0, len(x), step)],
            [dates[i] for i in range(0, len(dates), step)]
        )

        chart_plot.refresh()

        # 가격 테이블 생성
        table_text = self._create_price_table(self.df.head(20))
        price_data.update(table_text)

    def _create_price_table(self, df: pd.DataFrame) -> str:
        """가격 테이블 생성"""
        if df.empty:
            return "데이터 없음"

        lines = []
        lines.append("=" * 80)
        lines.append(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>12}")
        lines.append("=" * 80)

        for _, row in df.iterrows():
            date_str = row['timestamp'].strftime('%Y-%m-%d')
            lines.append(
                f"{date_str:<12} "
                f"${row['open']:>9.2f} "
                f"${row['high']:>9.2f} "
                f"${row['low']:>9.2f} "
                f"${row['close']:>9.2f} "
                f"{int(row['volume']):>12,}"
            )

        lines.append("=" * 80)
        return "\n".join(lines)

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        """뒤로 가기 버튼 클릭"""
        self.action_back()

    @on(Button.Pressed, "#refresh-button")
    def on_refresh_button_pressed(self) -> None:
        """새로고침 버튼 클릭"""
        self.action_refresh()

    def action_back(self) -> None:
        """뒤로 가기 액션"""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """새로고침 액션"""
        self.run_worker(self.load_stock_data())
