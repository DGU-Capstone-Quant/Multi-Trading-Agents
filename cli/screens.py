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


def _make_progress_key(ticker: str, trade_date: str) -> str:
    """거래 진행 상황 캐시 키 생성"""
    return f"trade_progress_{ticker}_{trade_date}"


# ============================================================================
# Main Screen
# ============================================================================

class MainScreen(BaseScreen):
    """메인 대시보드 화면"""

    class DebateCompleted(Message):
        """개별 토론 완료 메시지"""
        def __init__(self, ticker: str, trade_date: str) -> None:
            super().__init__()
            self.ticker = ticker
            self.trade_date = trade_date

    class AllDebatesCompleted(Message):
        """전체 토론 완료 메시지"""
        def __init__(self, trade_date: str, completed: list, failed: list) -> None:
            super().__init__()
            self.trade_date = trade_date
            self.completed = completed
            self.failed = failed

    class PlanPreview(Message):
        """투자 계획 프리뷰 업데이트 메시지"""
        def __init__(self, event: str, payload: dict) -> None:
            super().__init__()
            self.event = event
            self.payload = payload
            self.ticker = payload.get("ticker", "")
            self.trade_date = payload.get("trade_date", "")

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

    #plan-preview-panel {
        height: 18;
        background: $panel;
        border: solid $secondary;
        padding: 1;
    }

    #plan-preview-title {
        height: 3;
        text-style: bold;
        color: $accent;
        content-align: center middle;
        border-bottom: solid $primary;
        margin-bottom: 1;
    }

    #plan-preview-body {
        color: $text;
        text-align: left;
    }
    """

    BINDINGS = [
        ("q", "quit", "종료"),
        ("r", "refresh", "새로고침"),
        ("d", "debate", "토론 실행"),
    ]

    def __init__(self, context: Context, date_ticker_map: dict):
        super().__init__(context)
        self.debate_manager = DebateManager(context, date_ticker_map)
        self.rapid_api_key = os.getenv("RAPID_API_KEY", "")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.time_remaining = 60
        self.total_interval = 60
        self.plan_preview_state = {
            "ticker": "",
            "trade_date": "",
            "plan": "",
            "decision": "",
            "recommendation": "",
            "status": "거래 계획이 생성되면 이 영역에 표시됩니다.",
        }

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
            with Vertical(id="left-panel"):
                yield PortfolioWidget(self.context, id="portfolio-widget")

            with Vertical(id="right-panel"):
                yield ActivityWidget(self.context, id="activity-widget")
                with Container(id="plan-preview-panel"):
                    yield Static("거래 계획 프리뷰", id="plan-preview-title")
                    with VerticalScroll(id="plan-preview-scroll"):
                        yield Static(
                            self.plan_preview_state.get("status", ""),
                            id="plan-preview-body",
                        )

        with Horizontal(id="control-bar"):
            yield Static(f"⏱ 다음 자동 거래: {self._format_time(self.time_remaining)}", id="timer-info")
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


    def _debate_progress_callback(self, event: str, payload: dict) -> None:
        """백그라운드 스레드에서 UI 메시지 전송"""
        self.post_message(self.PlanPreview(event, payload))

    def _reset_plan_preview(self, status: str = "거래 계획이 생성되면 이 영역에 표시됩니다.") -> None:
        """프리뷰 영역 초기화"""
        self.plan_preview_state = {
            "ticker": "",
            "trade_date": "",
            "plan": "",
            "decision": "",
            "recommendation": "",
            "status": status,
        }
        self._refresh_plan_preview_panel()

    def _build_plan_preview_text(self) -> str:
        """프리뷰 텍스트 구성"""
        status = self.plan_preview_state.get("status", "")
        plan = (self.plan_preview_state.get("plan") or "").strip()
        decision = (self.plan_preview_state.get("decision") or "").strip()
        recommendation = (self.plan_preview_state.get("recommendation") or "").strip()

        if not plan and not decision and not recommendation:
            return status or "거래 계획이 생성되면 이 영역에 표시됩니다."

        lines = []

        if plan:
            lines.append(plan)

        supplemental = []
        if decision:
            supplemental.append(f"결정: {decision}")
        if recommendation:
            supplemental.append(f"추천: {recommendation}")

        if supplemental:
            if lines:
                lines.append("")
            lines.append("=== Trader Summary ===")
            lines.extend(supplemental)

        return "\n".join(lines)

    def _refresh_plan_preview_panel(self) -> None:
        """프리뷰 위젯 업데이트"""
        try:
            title = self.query_one("#plan-preview-title", Static)
            body = self.query_one("#plan-preview-body", Static)
        except Exception:
            return

        ticker = self.plan_preview_state.get("ticker", "")
        trade_date = self.plan_preview_state.get("trade_date", "")

        if ticker and trade_date:
            title_text = f"거래 계획 프리뷰 · {trade_date} / {ticker}"
        else:
            title_text = "거래 계획 프리뷰"

        title.update(title_text)
        body.update(self._build_plan_preview_text())
        self._trigger_activity_refresh()

    def _cache_trade_progress(self, ticker: str, trade_date: str, **updates) -> None:
        """거래 진행 상황 캐시 저장"""
        if not ticker or not trade_date:
            return

        key = _make_progress_key(ticker, trade_date)
        progress = self.context.get_cache(key, {})
        progress.setdefault("ticker", ticker)
        progress.setdefault("trade_date", trade_date)
        progress.update(updates)

        keys = list(self.context.get_cache("trade_progress_keys", []))
        if key not in keys:
            keys.append(key)

        self.context.set_cache(**{key: progress, "trade_progress_keys": keys})
        self._trigger_activity_refresh()

    def _trigger_activity_refresh(self) -> None:
        """거래 내역 위젯 새로고침 트리거"""
        try:
            widget = self.query_one("#activity-widget", ActivityWidget)
            self.run_worker(widget.refresh_data(), group="activity-widget", exclusive=True)
        except Exception:
            pass

    def on_auto_refresh(self) -> None:
        """자동 토론 실행 (1분마다)"""
        self.time_remaining = self.total_interval
        self.run_auto_debate()

    def run_auto_debate(self) -> None:
        """자동 토론 실행"""
        # API 키 검증
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
        self._reset_plan_preview(f"{trade_date} 거래 계획 생성 대기 중...")

        # 진행 상황 초기화
        for item in items:
            self._cache_trade_progress(
                item["ticker"],
                item["trade_date"],
                status="debate_in_progress",
                plan="",
                decision="",
                recommendation="",
            )

        # 백그라운드 스레드에서 토론 실행
        import threading

        def run_debates():
            completed = []
            failed = []

            for item in items:
                try:
                    success = self.debate_manager.run_debate(
                        item["ticker"],
                        item["trade_date"],
                        progress_callback=self._debate_progress_callback,
                    )
                    if success:
                        completed.append(item["ticker"])
                        self.post_message(self.DebateCompleted(item["ticker"], item["trade_date"]))
                    else:
                        failed.append(item["ticker"])
                except Exception:
                    failed.append(item["ticker"])

            self.post_message(self.AllDebatesCompleted(trade_date, completed, failed))

        threading.Thread(target=run_debates, daemon=True).start()

    @on(DebateCompleted)
    async def handle_debate_completed(self, message: DebateCompleted) -> None:
        """개별 토론 완료 핸들러"""
        try:
            activity_widget = self.query_one("#activity-widget", ActivityWidget)
            await activity_widget.refresh_data()
            self.update_status(f"✅ 토론 완료: {message.ticker} ({message.trade_date})")
        except Exception:
            pass

    @on(AllDebatesCompleted)
    async def handle_all_debates_completed(self, message: AllDebatesCompleted) -> None:
        """전체 토론 완료 핸들러"""
        total = len(message.completed) + len(message.failed)

        if message.failed:
            self.update_status(f"⚠️ 토론 완료: {message.trade_date} - 성공 {len(message.completed)}/{total}, 실패 {len(message.failed)}/{total}")
            self.notify(f"토론 완료: {message.trade_date}\n성공: {', '.join(message.completed)}\n실패: {', '.join(message.failed)}", severity="warning")
        else:
            self.update_status(f"✅ 토론 완료: {message.trade_date} - {len(message.completed)}개 종목 모두 성공")
            self.notify(f"토론 완료: {message.trade_date} - {', '.join(message.completed)}", severity="information")

        await self.refresh_data()

    @on(PlanPreview)
    async def handle_plan_preview(self, message: PlanPreview) -> None:
        """투자 계획 프리뷰 업데이트 핸들러"""
        if message.event == "investment_plan_ready":
            self.plan_preview_state.update({
                "ticker": message.ticker,
                "trade_date": message.trade_date,
                "plan": message.payload.get("plan", ""),
                "decision": "",
                "recommendation": "",
                "status": "",
            })
            self.update_status(f"💡 계획 준비 완료: {message.ticker} ({message.trade_date})")
            self._cache_trade_progress(message.ticker, message.trade_date, plan=message.payload.get("plan", ""), decision="", recommendation="", status="plan_ready")
        elif message.event == "trader_finished":
            if message.ticker:
                self.plan_preview_state["ticker"] = message.ticker
            if message.trade_date:
                self.plan_preview_state["trade_date"] = message.trade_date

            self.plan_preview_state["decision"] = message.payload.get("decision", "")
            self.plan_preview_state["recommendation"] = message.payload.get("recommendation", "")
            self.plan_preview_state["status"] = ""
            self.update_status(f"✅ 트레이더 결정: {message.ticker} ({message.trade_date})")
            self._cache_trade_progress(message.ticker, message.trade_date, plan=self.plan_preview_state.get("plan", ""), decision=message.payload.get("decision", ""), recommendation=message.payload.get("recommendation", ""), status="completed")

        self._refresh_plan_preview_panel()


    async def refresh_data(self) -> None:
        """전체 데이터 새로고침"""
        portfolio_widget = self.query_one("#portfolio-widget", PortfolioWidget)
        await portfolio_widget.refresh_data()

        activity_widget = self.query_one("#activity-widget", ActivityWidget)
        await activity_widget.refresh_data()

        self.update_status("데이터 새로고침 완료")

    def update_status(self, message: str) -> None:
        """상태 메시지 업데이트 (확장 가능)"""
        _ = message

    @on(Button.Pressed, "#manual-debate-btn")
    def on_manual_debate_pressed(self) -> None:
        self.action_debate()

    def action_debate(self) -> None:
        """수동 토론 실행"""
        self.run_auto_debate()
        self.time_remaining = self.total_interval

    async def action_refresh(self) -> None:
        """수동 새로고침"""
        await self.refresh_data()
        self.notify("데이터 새로고침 완료", severity="information")

    def action_quit(self) -> None:
        """앱 종료"""
        self.app.exit()


# ============================================================================
# Debate Detail Screen
# ============================================================================

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
        yield Button(f"▶ {self.title} (클릭하여 펼치기)", id=f"toggle-{self.report_type}", classes="report-toggle-button")
        yield Container(id=f"content-{self.report_type}", classes="content-wrapper")

    def _format_content(self, content: str) -> str:
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
        """보고서 펼치기/접기 토글"""
        self.is_expanded = not self.is_expanded

        button = self.query_one(f"#toggle-{self.report_type}", Button)
        content_wrapper = self.query_one(f"#content-{self.report_type}", Container)

        if self.is_expanded:
            button.label = f"▼ {self.title} (클릭하여 접기)"
            content_static = Static(self._format_content(self.content), classes="report-content")
            await content_wrapper.mount(VerticalScroll(content_static, classes="report-content-container"))
            self.content_widget = content_static
        else:
            button.label = f"▶ {self.title} (클릭하여 펼치기)"
            await content_wrapper.remove_children()
            self.content_widget = None

    def set_content(self, content: str) -> None:
        """보고서 내용 업데이트"""
        self.content = content
        if self.is_expanded and self.content_widget:
            self.content_widget.update(self._format_content(content))


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
                        "시장 보고서",
                        market_report,
                        "market_report"
                    )

                # investment_plan
                investment_plan = self._get_report("investment_plan")
                if investment_plan:
                    yield ReportToggle(
                        "투자 계획",
                        investment_plan,
                        "investment_plan"
                    )

                # trader_decision
                trader_decision = self._get_report("trader_decision")
                if trader_decision:
                    yield ReportToggle(
                        "트레이더 결정",
                        trader_decision,
                        "trader_decision"
                    )

            # 뒤로 가기 버튼
            yield Button("← 뒤로 가기", id="back-button", variant="warning")

        yield Footer()

    def _get_report(self, report_type: str) -> str:
        """Context에서 보고서 가져오기"""
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

            return f"**결정:**\n{decision}\n\n**추천:**\n{recommendation}"

        key = f"{self.ticker}_{self.trade_date}_{report_type}"
        content = self.context.get_report(key)
        if not content:
            return f"[{report_type}] 보고서를 찾을 수 없습니다.\n(키: {key})"

        return content

    @on(Button.Pressed, ".report-toggle-button")
    async def on_toggle_button_pressed(self, event: Button.Pressed) -> None:
        """보고서 토글 버튼 클릭 처리"""
        toggle_widget = event.button.parent
        if isinstance(toggle_widget, ReportToggle):
            await toggle_widget.toggle()

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        self.action_back()

    def action_back(self) -> None:
        """이전 화면으로 돌아가기"""
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

    #trade-history {
        height: auto;
        background: $surface;
        border: solid $secondary;
        padding: 1 2;
        margin-top: 1;
    }

    .trade-history-text {
        color: $text;
        background: $surface;
    }

    .trade-history-item {
        width: 100%;
        margin: 0 0 1 0;
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

            # 거래 이력
            yield VerticalScroll(id="trade-history")

            # 버튼 컨테이너
            with Horizontal(id="button-container"):
                yield Button("← 뒤로 가기", id="back-button", variant="warning")
                yield Button("🔄 새로고침", id="refresh-button", variant="primary")

        yield Footer()

    async def on_mount(self) -> None:
        """마운트 시 데이터 로드"""
        await self.load_stock_data()
        await self.refresh_trade_history()
        self.set_interval(3, self._schedule_trade_history_refresh)

    async def load_stock_data(self) -> None:
        """주가 데이터 로드 및 차트 표시"""
        try:
            await self.refresh_trade_history()
            date_to = datetime.now().strftime("%Y-%m-%d")
            date_from = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

            self.df = fetch_time_series_daily(ticker=self.ticker, date_from=date_from, date_to=date_to)

            if self.df is None or self.df.empty:
                chart_plot = self.query_one("#chart-plot", PlotextPlot)
                chart_plot.plt.clear_data()
                chart_plot.plt.clear_figure()
                chart_plot.plt.title(f"{self.ticker} 데이터를 사용할 수 없습니다")
                chart_plot.refresh()
                return

            self.display_chart()

        except Exception as e:
            chart_plot = self.query_one("#chart-plot", PlotextPlot)
            chart_plot.plt.clear_data()
            chart_plot.plt.clear_figure()
            chart_plot.plt.title(f"오류: {str(e)}")
            chart_plot.refresh()

    def display_chart(self) -> None:
        """주가 차트 렌더링"""
        if self.df is None or self.df.empty:
            return

        chart_plot = self.query_one("#chart-plot", PlotextPlot)
        df_chart = self.df.head(60).copy()
        df_chart = df_chart.sort_values('timestamp')

        dates = df_chart['timestamp'].dt.strftime('%Y-%m-%d').tolist()
        close_prices = df_chart['close'].tolist()
        x = list(range(len(df_chart)))

        plt_obj = chart_plot.plt
        plt_obj.clear_data()
        plt_obj.clear_figure()
        plt_obj.plot(x, close_prices, label="종가", marker="braille")
        plt_obj.title(f"{self.ticker} 주가 (최근 60일)")
        plt_obj.xlabel("날짜")
        plt_obj.ylabel("가격 ($)")

        step = max(1, len(x) // 10)
        plt_obj.xticks([x[i] for i in range(0, len(x), step)], [dates[i] for i in range(0, len(dates), step)])

        chart_plot.refresh()

    async def refresh_trade_history(self) -> None:
        """거래 이력 목록 새로고침"""
        try:
            container = self.query_one("#trade-history", VerticalScroll)
        except Exception:
            return

        for child in list(container.children):
            await child.remove()

        entries = self._collect_trade_history_entries()

        if not entries:
            await container.mount(Static("거래 내역이 없습니다.", classes="trade-history-text"))
            return

        for entry in entries:
            button_id = f"trade-history__{entry['ticker']}__{entry['trade_date']}"
            variant = "warning" if entry["is_active"] else "primary"
            label = self._build_trade_history_label(entry)
            await container.mount(Button(label, id=button_id, classes="trade-history-item", variant=variant))

    def _collect_trade_history_entries(self) -> list:
        """Context에서 현재 ticker의 거래 내역 수집"""
        entries = []
        seen = set()
        progress_keys = self.context.get_cache("trade_progress_keys", [])

        for key in progress_keys:
            data = self.context.get_cache(key, {})
            ticker = data.get("ticker")
            trade_date = data.get("trade_date")
            if ticker != self.ticker:
                continue
            trade_id = f"{ticker}_{trade_date}"
            seen.add(trade_id)
            entries.append({
                "ticker": ticker,
                "trade_date": trade_date,
                "status": data.get("status", "progress"),
                "decision": data.get("decision", ""),
                "recommendation": data.get("recommendation", ""),
                "is_active": data.get("status", "") != "completed",
            })

        completed_debates = self.context.get_cache("completed_debates", [])
        for debate in completed_debates:
            ticker = debate.get("ticker")
            trade_date = debate.get("trade_date")
            if ticker != self.ticker:
                continue
            trade_id = f"{ticker}_{trade_date}"
            if trade_id in seen:
                continue
            decision_key = f"{ticker}_{trade_date}_trader_decision"
            recommendation_key = f"{ticker}_{trade_date}_trader_recommendation"
            entries.append({
                "ticker": ticker,
                "trade_date": trade_date,
                "status": "completed",
                "decision": self.context.get_cache(decision_key, ""),
                "recommendation": self.context.get_cache(recommendation_key, ""),
                "is_active": False,
            })

        entries.sort(key=lambda x: (x["is_active"], x["trade_date"]), reverse=True)
        return entries[:10]

    def _build_trade_history_label(self, entry: dict) -> str:
        """거래 이력 항목 라벨 생성"""
        status = entry.get("status", "")
        if status == "plan_ready":
            status_label = "트레이더 검토 중"
        elif status == "debate_in_progress":
            status_label = "토론 진행 중"
        elif status == "completed":
            status_label = entry.get("decision") or "거래 완료"
        else:
            status_label = "진행 중"

        return f"{entry['trade_date']} - {entry['ticker']} ({status_label})"

    def _schedule_trade_history_refresh(self) -> None:
        """주기적으로 거래 이력 새로고침"""
        self.run_worker(self.refresh_trade_history(), exclusive=True, group="trade-history")

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        self.action_back()

    @on(Button.Pressed, "#refresh-button")
    def on_refresh_button_pressed(self) -> None:
        self.action_refresh()

    def action_back(self) -> None:
        """이전 화면으로 돌아가기"""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """주가 데이터 새로고침"""
        self.run_worker(self.load_stock_data())

    @on(Button.Pressed, ".trade-history-item")
    def on_trade_history_item_pressed(self, event: Button.Pressed) -> None:
        """거래 이력 클릭 시 진행 상황 화면으로 이동"""
        button_id = event.button.id or ""
        if not button_id.startswith("trade-history__"):
            return

        parts = button_id.split("__", 2)
        if len(parts) < 3:
            return

        _, ticker, trade_date = parts

        self.app.push_screen(TradeProgressScreen(self.context, ticker, trade_date))


# ============================================================================
# Trade Progress Screen
# ============================================================================

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

    BINDINGS = [
        ("escape", "back", "뒤로 가기"),
    ]

    def __init__(self, context: Context, ticker: str, trade_date: str, *args, **kwargs):
        super().__init__(context, *args, **kwargs)
        self.ticker = ticker
        self.trade_date = trade_date
        self.market_toggle: ReportToggle | None = None
        self.plan_toggle: ReportToggle | None = None
        self.trader_toggle: ReportToggle | None = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="progress-container"):
            with Container(id="progress-header"):
                yield Static(
                    f"거래 진행 상황 · {self.trade_date} / {self.ticker}",
                    id="progress-title",
                    classes="chart-text",
                )

            yield Static("", id="progress-status")

            with VerticalScroll(id="reports-container"):
                self.market_toggle = ReportToggle("시장 보고서", "시장 보고서를 아직 사용할 수 없습니다.", "tp_market_report")
                self.plan_toggle = ReportToggle("투자 계획", "투자 계획이 아직 생성되지 않았습니다.", "tp_investment_plan")
                self.trader_toggle = ReportToggle("트레이더 결정", "트레이더 결정 대기 중입니다.", "tp_trader_decision")
                yield self.market_toggle
                yield self.plan_toggle
                yield self.trader_toggle

            yield Button("← 뒤로 가기", id="progress-back-button", variant="warning")

        yield Footer()

    async def on_mount(self) -> None:
        """마운트 시 데이터 로드 및 자동 새로고침 시작"""
        self.set_interval(2, lambda: self.run_worker(self.refresh_content(), group="trade-progress", exclusive=True))
        await self.refresh_content()

    async def refresh_content(self) -> None:
        """Context 데이터를 사용하여 UI 업데이트"""
        data = self._get_progress_data()

        status_widget = self.query_one("#progress-status", Static)
        status_widget.update(self._format_status_text(data))

        if self.market_toggle:
            self.market_toggle.set_content(data.get("market_report") or "시장 보고서를 사용할 수 없습니다.")
        if self.plan_toggle:
            plan_content = data.get("plan") or "투자 계획을 사용할 수 없습니다."
            self.plan_toggle.set_content(plan_content)
        if self.trader_toggle:
            if data.get("decision") or data.get("recommendation"):
                decision_text = f"**결정:** {data.get('decision','')}\n\n**추천:**\n{data.get('recommendation','')}"
            else:
                decision_text = "트레이더 결정 대기 중입니다."
            self.trader_toggle.set_content(decision_text)

    def _format_status_text(self, data: dict) -> str:
        """상태 텍스트 포맷"""
        status = data.get("status", "")
        if status == "debate_in_progress":
            return "상태: 토론 진행 중"
        if status == "plan_ready":
            return "상태: 토론 완료 - 트레이더 검토 중"
        if status == "completed":
            return "상태: 거래 완료"
        return "상태: 준비 중"

    def _get_progress_data(self) -> dict:
        """Context에서 진행 상황 데이터 가져오기"""
        key = _make_progress_key(self.ticker, self.trade_date)
        data = self.context.get_cache(key, {})

        market_report = self.context.get_report(f"{self.ticker}_{self.trade_date}_market_report") or self.context.get_report("market_report")
        plan = self.context.get_report(f"{self.ticker}_{self.trade_date}_investment_plan") or self.context.get_report("investment_plan")
        decision = self.context.get_cache(f"{self.ticker}_{self.trade_date}_trader_decision", "")
        recommendation = self.context.get_cache(f"{self.ticker}_{self.trade_date}_trader_recommendation", "")

        if not data:
            status = "completed" if decision else "unknown"
            data = {"ticker": self.ticker, "trade_date": self.trade_date, "status": status}

        data["market_report"] = market_report
        data["plan"] = plan
        data["decision"] = decision
        data["recommendation"] = recommendation

        return data

    @on(Button.Pressed, "#progress-back-button")
    def on_back_pressed(self) -> None:
        self.action_back()

    def action_back(self) -> None:
        """이전 화면으로 돌아가기"""
        self.app.pop_screen()

    @on(Button.Pressed, ".report-toggle-button")
    async def on_toggle_button_pressed(self, event: Button.Pressed) -> None:
        """보고서 토글 버튼 클릭 처리"""
        toggle_widget = event.button.parent
        if isinstance(toggle_widget, ReportToggle):
            await toggle_widget.toggle()
