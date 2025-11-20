"""메인 대시보드 화면"""

import os
import threading
from datetime import datetime
from typing import Dict
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, Label
from textual.containers import Container, Horizontal, Vertical
from textual import on

from modules.context import Context
from cli.base import BaseScreen
from cli.widgets import PortfolioWidget, ActivityWidget
from graphs.rank import create_rank_graph
from graphs.debate.factory import create_debate_graph
from cli.screens.utils import get_report_from_context, make_progress_key
from cli.events import ContextUpdated

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

    def __init__(self, context: Context, date_ticker_map: Dict[str, list[str]]):
        super().__init__(context)
        self.date_ticker_map = date_ticker_map
        self.sorted_dates = sorted(date_ticker_map.keys())
        self.current_date_index = 0
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

        tickers = [t.strip().upper() for t in ticker_input.split(",")] if ticker_input else ["AAPL", "GOOGL", "MSFT"]

        trade_date = None
        if self.use_realtime:
            # 실시간 모드가 켜져 있으면 입력 날짜보다 실시간을 우선
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

        threading.Thread(target=lambda: self._run_graph(tickers, trade_date), daemon=True).start()

    def _format_graph_date(self, trade_date: str) -> str:
        """그래프 노드에서 요구하는 YYYYMMDDTHHMM 포맷으로 변환."""
        try:
            dt_obj = datetime.strptime(trade_date, "%Y-%m-%d")
        except ValueError:
            dt_obj = datetime.now()
        return dt_obj.strftime("%Y%m%dT%H%M")

    def _init_trade_progress(self, tickers: list, trade_date: str) -> None:
        """그래프 시작 시 진행중 상태를 등록해 중간에도 조회 가능하게 한다."""
        keys = self.context.get_cache("trade_progress_keys", []) or []
        for ticker in tickers:
            progress_key = make_progress_key(ticker, trade_date)
            data = self.context.get_cache(progress_key, {}) or {"ticker": ticker, "trade_date": trade_date}
            data.setdefault("status", "debate_in_progress")
            self.context.set_cache(**{progress_key: data})
            if progress_key not in keys:
                keys.append(progress_key)
        self.context.set_cache(trade_progress_keys=keys)

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

    def _extract_decision(self, plan_text: str, ticker: str) -> str:
        if not plan_text:
            return f"{ticker} 분석 완료"

        for line in plan_text.splitlines():
            normalized = line.strip()
            if not normalized:
                continue
            lower_line = normalized.lower()
            if "decision" in lower_line:
                value = normalized.split(":", 1)[-1].strip(" *")
                return value if value else normalized

        return plan_text.splitlines()[0]

    def _normalize_portfolio(self) -> dict:
        portfolio = self.context.get_cache("portfolio", {}) or {}
        if isinstance(portfolio, dict):
            return portfolio
        if isinstance(portfolio, (list, set, tuple)):
            normalized = {str(ticker): {"source": "legacy"} for ticker in portfolio if isinstance(ticker, str)}
            self.context.set_cache(portfolio=normalized)
            return normalized
        self.context.set_cache(portfolio={})
        return {}

    def _add_portfolio_ticker(self, ticker: str, trade_date: str) -> None:
        portfolio = self._normalize_portfolio()
        if ticker not in portfolio:
            portfolio[ticker] = {"added_at": trade_date}
            self.context.set_cache(portfolio=portfolio)

    def _run_graph(self, tickers: list, trade_date: str) -> None:
        graph_date = self._format_graph_date(trade_date)
        self._normalize_portfolio()

        try:
            self.context.set_config(
                analysis_tasks=["financial"],
                tickers=tickers,
                max_portfolio_size=max(1, len(tickers)),
                rounds=2,
            )
            # 그래프에서 None 목록을 다루며 len 호출로 터지는 것을 방지하기 위해 기본 리스트 값 세팅
            self.context.set_cache(date=graph_date, tickers=tickers, display_date=trade_date, candidates=[])
            # 진행 중 상태 등록
            self._init_trade_progress(tickers, trade_date)
            self.app.call_from_thread(lambda: self.app.post_message(ContextUpdated()))
            self.app.call_from_thread(self._refresh_widgets)

            rank_graph = create_rank_graph()
            self.context = rank_graph.run(self.context)
            recommended = self.context.get_cache("recommendation", tickers) or tickers
            self.context.set_cache(tickers=recommended)
            # 랭킹 결과를 포트폴리오에 즉시 반영해 진행 중에도 보이게 함
            for rec in recommended:
                self._add_portfolio_ticker(rec, trade_date)
            self.app.call_from_thread(lambda: self.app.post_message(ContextUpdated()))
            self.app.call_from_thread(self._refresh_widgets)

            debate_graph = create_debate_graph()
            self.context = debate_graph.run(self.context)

            for ticker in recommended:
                plan_text = get_report_from_context(self.context, ticker, trade_date, "investment_plan") or ""
                decision = self._extract_decision(plan_text, ticker)
                recommendation = plan_text or f"{ticker}에 대한 투자 계획을 확인할 수 없습니다."
                self._record_trade(ticker, trade_date, decision, recommendation)

            self.app.call_from_thread(
                self.notify,
                f"[OK] 그래프 실행 완료 | 종목: {', '.join(recommended)}",
                severity="success",
            )
        except Exception as e:
            for ticker in tickers:
                fallback_decision = f"{ticker} 분석 실패"
                fallback_recommendation = f"그래프 실행 실패: {str(e)[:80]}"
                self._record_trade(ticker, trade_date, fallback_decision, fallback_recommendation)
            self.app.call_from_thread(
                self.notify,
                f"[ERR] 그래프 실행 실패: {str(e)[:80]}",
                severity="error",
            )

        self.app.call_from_thread(self._refresh_widgets)

    def _record_trade(self, ticker: str, trade_date: str, decision: str, recommendation: str) -> None:
        decision_key = f"{ticker}_{trade_date}_trader_decision"
        recommendation_key = f"{ticker}_{trade_date}_trader_recommendation"

        # 투자 계획이 아직 준비되지 않은 경우에는 빈 값으로 두어 나중에 덮어쓸 수 있게 함
        clean_decision = decision
        clean_reco = recommendation
        if "투자 계획 보고서를 찾을 수 없습니다" in (clean_reco or ""):
            clean_decision = ""
            clean_reco = ""

        self.context.set_cache(
            **{
                "trader_decision": clean_decision,
                "trader_recommendation": clean_reco,
                decision_key: clean_decision,
                recommendation_key: clean_reco,
            }
        )

        # 진행 상태 업데이트 (완료)
        progress_key = make_progress_key(ticker, trade_date)
        progress_data = self.context.get_cache(progress_key, {}) or {"ticker": ticker, "trade_date": trade_date}
        progress_data.update({
            "status": "completed",
            "decision": clean_decision,
            "recommendation": clean_reco,
        })
        keys = self.context.get_cache("trade_progress_keys", []) or []
        if progress_key not in keys:
            keys.append(progress_key)
        self.context.set_cache(trade_progress_keys=keys, **{progress_key: progress_data})

        debates = self.context.get_cache("completed_debates", []) or []
        if not any(d.get("ticker") == ticker and d.get("trade_date") == trade_date for d in debates):
            debates.append({"ticker": ticker, "trade_date": trade_date})
            self.context.set_cache(completed_debates=debates)

        self._add_portfolio_ticker(ticker, trade_date)
        # 컨텍스트 변경을 즉시 UI에 반영
        self.app.call_from_thread(lambda: self.app.post_message(ContextUpdated()))
        self.app.call_from_thread(self._refresh_widgets)

    def action_quit(self) -> None:
        self.app.exit()





