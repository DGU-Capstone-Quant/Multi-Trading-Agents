"""메인 대시보드 화면"""

import os
import threading
from datetime import datetime
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, Label
from textual.containers import Container, Horizontal, Vertical
from textual import on

from modules.context import Context
from cli.base import BaseScreen
from cli.widgets import PortfolioWidget, ActivityWidget
from cli.events import ContextUpdated
from graphs.main.graph import create_main_graph

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")


class MainScreen(BaseScreen):
    """메인 대시보드 화면"""

    CSS = """
    MainScreen {
        layout: vertical;
        background: $surface;
    }

    #top-section {
        layout: vertical;
        background: $boost;
        border: heavy $primary;
        padding: 1;
        margin-bottom: 1;
        content-align: left top;
        min-height: 14;
    }

    #api-row {
        layout: horizontal;
        width: 1fr;
        align: left middle;
        height: 3;
        min-height: 3;
        margin-bottom: 0;
    }

    .api-key-group {
        layout: horizontal;
        width: auto;
        min-width: 32;
        margin-right: 2;
    }

    .api-key-group:last-child {
        margin-right: 0;
    }

    .api-key-label {
        width: 12;
        color: $accent;
        text-style: bold;
        padding-right: 1;
    }

    .api-key-input {
        width: 32;
        min-width: 32;
        max-width: 32;
    }

    .api-key-status {
        width: 2;
        margin-left: 1;
    }

    #main-content {
        layout: horizontal;
        height: 1fr;
    }

    #left-panel, #right-panel {
        width: 50%;
        height: 100%;
        background: $boost;
        border: heavy $primary;
        padding: 1;
    }

    #left-panel {
        margin-right: 1;
    }

    #control-row {
        layout: vertical;
        width: 1fr;
        align: left top;
        height: auto;
        min-height: 6;
        margin-top: 1;
        padding-bottom: 1;
    }

    #control-inputs {
        layout: horizontal;
        width: 1fr;
        align: left middle;
        height: auto;
        min-height: 3;
    }

    #control-actions {
        layout: horizontal;
        width: auto;
        content-align: left middle;
        margin-top: 0;
        height: 3;
        min-height: 3;
    }

    #control-actions Button {
        margin-left: 0;
    }

    .control-field {
        margin-right: 1;
    }

    #control-inputs Input {
        margin-bottom: 1;
    }

    #ticker-input {
        width: 38;
        min-width: 38;
        max-width: 38;
        margin-right: 1;
    }

    #date-input {
        width: 34;
        min-width: 34;
        max-width: 34;
        margin-right: 1;
    }

    #control-spacer {
        width: 1fr;
    }

    .control-btn {
        min-width: 15;
        height: 3;
        padding: 0 3;
    }

    """

    BINDINGS = [("q", "quit", "종료"), ("d", "debate", "토론 실행")]

    def __init__(self, context: Context):
        super().__init__(context)
        self.use_realtime = True

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="top-section"):

            with Horizontal(id="api-row"):
                for api_name, env_key, input_id in [
                    ("RAPID API", "RAPID_API_KEY", "rapid-api-input"),
                    ("GOOGLE API", "GOOGLE_API_KEY", "google-api-input"),
                ]:
                    with Horizontal(classes="api-key-group"):
                        yield Label(f"{api_name}:", classes="api-key-label")
                        yield Input(
                            placeholder="API Key를 입력하세요",
                            password=True,
                            value=os.getenv(env_key, ""),
                            id=input_id,
                            classes="api-key-input",
                        )
                        yield Static("OK" if os.getenv(env_key) else "X", id=f"{input_id}-status", classes="api-key-status")

            with Horizontal(id="control-row"):
                with Horizontal(id="control-inputs"):
                    yield Label("종목:", classes="api-key-label control-field")
                    yield Input(
                        placeholder="예: AAPL, GOOGL (비우면 기본값)",
                        id="ticker-input",
                        classes="api-key-input control-field",
                    )
                    yield Label("날짜:", classes="api-key-label control-field")
                    yield Input(
                        placeholder="예: 2024-01-15 (비우면 오늘)",
                        id="date-input",
                        classes="api-key-input control-field",
                    )
                yield Static(id="control-spacer", expand=True)
                with Horizontal(id="control-actions"):
                    yield Button("[실시간] 모드 ON", id="realtime-btn", variant="primary", classes="control-btn")
                    yield Button("거래 실행 (Ctrl+D)", id="debate-btn", variant="success", classes="control-btn")

        with Horizontal(id="main-content"):
            with Vertical(id="left-panel"):
                yield PortfolioWidget(self.context, id="portfolio-widget")
            with Vertical(id="right-panel"):
                yield ActivityWidget(self.context, id="activity-widget")

        yield Footer()

    @on(Input.Changed, "#rapid-api-input")
    def on_rapid_api_changed(self, event: Input.Changed) -> None:
        os.environ["RAPID_API_KEY"] = event.value
        self.query_one("#rapid-api-input-status", Static).update("OK" if event.value else "X")

    @on(Input.Changed, "#google-api-input")
    def on_google_api_changed(self, event: Input.Changed) -> None:
        os.environ["GOOGLE_API_KEY"] = event.value
        self.query_one("#google-api-input-status", Static).update("OK" if event.value else "X")

    @on(Button.Pressed, "#realtime-btn")
    def on_realtime_pressed(self) -> None:
        self.use_realtime = not self.use_realtime
        btn = self.query_one("#realtime-btn", Button)
        if self.use_realtime:
            btn.label = "[실시간] 모드 ON"
            btn.variant = "primary"
        else:
            btn.label = "[날짜] 모드 ON"
            btn.variant = "warning"

    @on(Button.Pressed, "#debate-btn")
    def on_debate_pressed(self) -> None:
        if not os.getenv("RAPID_API_KEY") or not os.getenv("GOOGLE_API_KEY"):
            return self.notify("API 키를 먼저 입력해주세요 (RAPID API, GOOGLE API)", severity="error", timeout=5)

        ticker_input = self.query_one("#ticker-input", Input).value.strip()
        date_input = self.query_one("#date-input", Input).value.strip()

        if not ticker_input:
            return self.notify("종목을 입력해주세요 (예: AAPL, GOOGL)", severity="error", timeout=5)

        tickers = [t.strip().upper() for t in ticker_input.split(",")]
        tickers = [t for t in tickers if t]

        if not tickers:
            return self.notify("종목을 입력해주세요 (예: AAPL, GOOGL)", severity="error", timeout=5)

        trade_date = None
        if self.use_realtime:
            trade_date = datetime.now().strftime("%Y-%m-%d")
            self.notify(f"[실시간] 분석 시작 | 종목: {', '.join(tickers)} | 날짜: {trade_date}", severity="information", timeout=3)
        else:
            if date_input:
                try:
                    datetime.strptime(date_input, "%Y-%m-%d")
                    trade_date = date_input
                    self.notify(f"[백테스팅] 분석 시작 | 종목: {', '.join(tickers)} | 날짜: {trade_date}", severity="information", timeout=3)
                except ValueError:
                    return self.notify("날짜 형식 오류 (예: 2024-01-15)", severity="error", timeout=5)
            else:
                trade_date = datetime.now().strftime("%Y-%m-%d")
                self.notify(f"[오늘 날짜] 분석 시작 | 종목: {', '.join(tickers)} | 날짜: {trade_date}", severity="information", timeout=3)

        self.context.set_config(tickers=tickers, trade_date=trade_date)
        self.context.on_update = self._notify_context_update
        threading.Thread(target=self._run_graph, daemon=True).start()

    def _refresh_widgets(self) -> None:
        """컨텍스트 변경 시 즉시 UI를 갱신"""
        try:
            activity = self.query_one("#activity-widget")
            activity.run_worker(activity.refresh_data())
        except Exception:
            pass
        try:
            portfolio = self.query_one("#portfolio-widget")
            portfolio.run_worker(portfolio.refresh_data())
        except Exception:
            pass

    def _notify_context_update(self) -> None:
        """Context 업데이트 콜백: 위젯/구독자 새로고침"""
        app_thread_id = getattr(self.app, "_thread_id", None)
        if app_thread_id and app_thread_id == threading.get_ident():
            self.app.post_message(ContextUpdated())
            self._refresh_widgets()
        else:
            self.app.call_from_thread(lambda: self.app.post_message(ContextUpdated()))
            self.app.call_from_thread(self._refresh_widgets)

    def _run_graph(self) -> None:
        self.context.on_update = self._notify_context_update
        graph = create_main_graph()
        graph.run(self.context)
        self.app.call_from_thread(self._refresh_widgets)

    def action_quit(self) -> None:
        self.app.exit()
