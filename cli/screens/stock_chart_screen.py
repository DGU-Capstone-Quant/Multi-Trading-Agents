"""주가 차트 화면"""

import plotext as plt
from datetime import datetime, timedelta
from typing import List, Dict, Any
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Container, Horizontal, VerticalScroll
from textual import on
from textual_plotext import PlotextPlot

from modules.context import Context
from modules.utils.fetch import fetch_time_series_intraday, fetch_time_series_daily, fetch_time_series_weekly
from cli.base import BaseScreen
from cli.events import ContextUpdated

def _trades_from_context_reports(context: Context, ticker: str) -> List[Dict[str, Any]]:
    """saved_context의 trader_decision 리포트로부터 거래 결정을 추출"""
    trades: List[Dict[str, Any]] = []
    reports = context.reports.get(ticker, {}) or {}
    for date_key, items in reports.items():
        decision_md = items.get("trader_decision", "")
        if not decision_md:
            continue
        # 날짜 키를 표시용으로 사용 (YYYYMMDDTHH -> YYYY-MM-DD HH:00)
        try:
            added_at = datetime.strptime(date_key, "%Y%m%dT%H").strftime("%Y-%m-%d %H:00")
        except Exception:
            added_at = date_key
        # 간단 파싱: 첫 번째 "**DECISION**" 라인에서 BUY/HOLD/SELL 추출
        decision = "N/A"
        quantity = None
        for line in str(decision_md).splitlines():
            if "**" in line and ("BUY" in line or "SELL" in line or "HOLD" in line):
                # 예: "**BUY** (Confidence: 80%)"
                for opt in ("BUY", "SELL", "HOLD"):
                    if opt in line:
                        decision = opt
                        break
            if "주" in line and "(" in line and ")" in line and "Confidence" not in line:
                # 간단히 숫자만 추출
                try:
                    qty_tokens = [s for s in line.split() if s.isdigit()]
                    if qty_tokens:
                        quantity = int(qty_tokens[0])
                except Exception:
                    quantity = None
        trades.append({
            "added_at": added_at,
            "decision": decision,
            "quantity": quantity,
            "confidence": None,
            "order_no": "CONTEXT",
        })
    return trades

# 차트 타입 옵션: (라벨, 타입, 기본 표시 범위)
CHART_TYPE_OPTIONS = [
    ("1시간봉", "hourly", 48),   # 48시간 (2일)
    ("일봉", "daily", 30),       # 30일
    ("주봉", "weekly", 52),      # 52주 (1년)
]

# 이동/확대 단위 (차트 타입별)
STEP_UNITS = {
    "hourly": 1,   # 1시간
    "daily": 1,    # 1일
    "weekly": 1,   # 1주
}

# 기본 표시 범위 (일수)
DEFAULT_RANGE = 30


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

    #button-container {
        layout: horizontal;
        height: auto;
        padding: 0 2;
    }

    #back-button, #refresh-button {
        width: 25;
        height: 3;
        margin: 1 1;
        text-style: bold;
    }

    #back-button {
        background: $warning;
    }

    #back-button:hover {
        background: $error;
        color: $text;
    }

    #refresh-button {
        background: $primary;
    }

    #refresh-button:hover {
        background: $accent;
        color: $text;
    }

    #control-container {
        layout: horizontal;
        height: auto;
        padding: 0 2;
        margin-bottom: 1;
    }

    .step-button {
        width: auto;
        min-width: 8;
        height: 3;
        margin: 0 1;
    }

    .step-button.active {
        background: $accent;
        text-style: bold;
    }

    .nav-button {
        width: auto;
        min-width: 6;
        height: 3;
        margin: 0 1;
    }

    #nav-separator-1, #nav-separator-2 {
        width: 2;
        height: 3;
    }

    #range-info {
        width: auto;
        height: 3;
        padding: 0 2;
        content-align: center middle;
    }
    """

    BINDINGS = [("escape", "back", "뒤로 가기"), ("r", "refresh", "새로고침")]

    def __init__(self, context: Context, ticker: str, *args, **kwargs):
        super().__init__(context, *args, **kwargs)
        self.ticker = str(ticker)  # Text 객체일 수 있으므로 str로 변환
        self.df = None
        self.current_chart_type = 0  # 차트 타입 (0: 일봉, 1: 주봉, 2: 월봉)
        self.end_date = datetime.now()  # 차트 끝 날짜 (현재)
        self.display_range = CHART_TYPE_OPTIONS[0][2]  # 표시 범위 (일봉 기본값)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="chart-container"):
            with Container(id="chart-header"):
                yield Static(f"{self.ticker} 주가 차트", id="chart-title")
                yield Static(f"Ticker: {self.ticker} | {self.end_date.strftime('%Y년 %m월 %d일')}", id="chart-info")
            with Horizontal(id="control-container"):
                # 차트 타입 선택 버튼 (일봉/주봉/월봉)
                for i, (label, _, _) in enumerate(CHART_TYPE_OPTIONS):
                    classes = "step-button active" if i == self.current_chart_type else "step-button"
                    yield Button(label, id=f"chart-type-{i}", classes=classes)
                yield Static("", id="nav-separator-1")
                # 좌우 이동 버튼
                yield Button("<<", id="nav-left", classes="nav-button")
                yield Button(">>", id="nav-right", classes="nav-button")
                yield Static("", id="nav-separator-2")
                # 확대/축소 버튼
                yield Button("-", id="zoom-out", classes="nav-button")
                yield Button("+", id="zoom-in", classes="nav-button")
                # 범위 표시
                yield Static(self._get_range_label(), id="range-info")
            with Container(id="chart-content"):
                yield PlotextPlot(id="chart-plot")
            yield VerticalScroll(id="trade-history")
            with Horizontal(id="button-container"):
                yield Button("< 뒤로 가기", id="back-button", variant="warning")
                yield Button("새로고침", id="refresh-button", variant="primary")
        yield Footer()

    async def on_mount(self) -> None:
        await self.load_stock_data()
        await self.refresh_trade_history()

    async def load_stock_data(self) -> None:
        """차트 타입에 따라 데이터를 로드 (1시간봉/일봉/주봉)"""
        try:
            _, chart_type, _ = CHART_TYPE_OPTIONS[self.current_chart_type]
            date_to = datetime.now().strftime("%Y-%m-%d")

            if chart_type == "hourly":
                self.df = fetch_time_series_intraday(
                    ticker=self.ticker,
                    interval="60min",
                )
            elif chart_type == "daily":
                self.df = fetch_time_series_daily(
                    ticker=self.ticker,
                    days=-1,
                    date_to=date_to,
                )
            elif chart_type == "weekly":
                self.df = fetch_time_series_weekly(
                    ticker=self.ticker,
                    weeks=-1,
                    date_to=date_to,
                )

            chart_plot = self.query_one("#chart-plot", PlotextPlot)
            chart_plot.plt.clear_data()
            chart_plot.plt.clear_figure()
            if self.df is None or self.df.empty:
                chart_plot.plt.title(f"{self.ticker} 데이터를 사용할 수 없습니다")
            else:
                self._render_chart(chart_plot)
            chart_plot.refresh()
        except Exception as e:
            self.query_one("#chart-plot", PlotextPlot).plt.title(f"오류: {str(e)}")

    def _render_chart(self, chart_plot) -> None:
        # end_date와 display_range를 사용하여 데이터 필터링
        df_chart = self.df.copy().sort_values('timestamp')
        _, chart_type, _ = CHART_TYPE_OPTIONS[self.current_chart_type]

        # 차트 타입에 따라 필터링 기간 계산
        if chart_type == "hourly":
            start_date = self.end_date - timedelta(hours=self.display_range)
        elif chart_type == "daily":
            start_date = self.end_date - timedelta(days=self.display_range)
        else:  # weekly
            start_date = self.end_date - timedelta(weeks=self.display_range)

        # 날짜 범위로 필터링
        df_filtered = df_chart[
            (df_chart['timestamp'] >= start_date) &
            (df_chart['timestamp'] <= self.end_date)
        ]

        if df_filtered.empty:
            # 데이터가 없으면 가장 최근 데이터 사용
            df_filtered = df_chart.tail(min(self.display_range, len(df_chart)))

        _, chart_type_str, _ = CHART_TYPE_OPTIONS[self.current_chart_type]
        if chart_type_str == "hourly":
            dates = df_filtered['timestamp'].dt.strftime('%m-%d %H:00').tolist()
        else:
            dates = df_filtered['timestamp'].dt.strftime('%Y-%m-%d').tolist()
        timestamps = [
            ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts
            for ts in df_filtered['timestamp'].tolist()
        ]
        close_prices = df_filtered['close'].tolist()

        x = list(range(len(df_filtered)))

        chart_plot.plt.plot(x, close_prices, marker="braille")

        buy_points_x, buy_points_y, sell_points_x, sell_points_y = [], [], [], []
        hold_points_x, hold_points_y = [], []

        # saved_context 보고서 + 캐시를 병합하여 거래 내역 구성 (파일은 사용하지 않음)
        trades_map: Dict[str, Dict[str, Any]] = {}
        # 우선순위: context < cache (나중에 들어온 것이 같은 날짜/시 키를 덮어씀)
        context_trades = _trades_from_context_reports(self.context, self.ticker)

        cache_portfolio = self.context.get_cache("portfolio", {}) or {}
        cache_trades = cache_portfolio.get(self.ticker, [])
        if isinstance(cache_trades, dict):
            cache_trades = [cache_trades]

        def _hour_key(dt_str: str) -> str:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:00", "%Y-%m-%d"):
                try:
                    return datetime.strptime(dt_str, fmt).strftime("%Y-%m-%d %H:00")
                except Exception:
                    continue
            return dt_str

        for source_trades in (context_trades, cache_trades):
            for t in source_trades or []:
                added_at = t.get("added_at")
                if not added_at:
                    continue
                trades_map[_hour_key(added_at)] = t

        trades = list(trades_map.values())

        # 리스트가 아니면 기존 형식 호환 (단일 dict인 경우)
        if isinstance(trades, dict):
            trades = [trades] if trades else []

        def _parse_trade_dt(dt_str: str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    return datetime.strptime(dt_str, fmt)
                except Exception:
                    continue
            return None

        for trade in trades:
            decision = (trade.get("decision", "") or "").upper()
            trade_date = trade.get("added_at", "")

            if not trade_date or not decision:
                continue

            # 차트에 없는 날짜면 가장 가까운 날짜로 매핑 (시/일/주봉 모두 지원)
            idx = None
            trade_dt = _parse_trade_dt(trade_date)
            if trade_dt and timestamps:
                idx = min(range(len(timestamps)), key=lambda i: abs(timestamps[i] - trade_dt))
            elif trade_date in dates:
                idx = dates.index(trade_date)

            if idx is not None:
                if "BUY" in decision:
                    buy_points_x.append(x[idx])
                    buy_points_y.append(close_prices[idx])
                elif "SELL" in decision:
                    sell_points_x.append(x[idx])
                    sell_points_y.append(close_prices[idx])
                elif "HOLD" in decision:
                    hold_points_x.append(x[idx])
                    hold_points_y.append(close_prices[idx])

        if buy_points_x:
            chart_plot.plt.scatter(buy_points_x, buy_points_y, marker="^", color="green")
        if sell_points_x:
            chart_plot.plt.scatter(sell_points_x, sell_points_y, marker="v", color="red")
        if hold_points_x:
            chart_plot.plt.scatter(hold_points_x, hold_points_y, marker="•", color="yellow")

        # 현재 날짜/범위 표시
        chart_label, _, _ = CHART_TYPE_OPTIONS[self.current_chart_type]
        end_str = self.end_date.strftime('%Y-%m-%d')
        range_label = self._get_range_label()
        chart_plot.plt.title(f"{self.ticker} {chart_label} ({range_label})  |  끝: {end_str}  |  BUY:^  SELL:v  HOLD:•")
        chart_plot.plt.xlabel("날짜")
        chart_plot.plt.ylabel("가격 ($)")

        # x축 라벨 설정
        if len(x) > 0:
            step = max(1, len(x) // 8)
            chart_plot.plt.xticks([x[i] for i in range(0, len(x), step)], [dates[i] for i in range(0, len(dates), step)])

    async def refresh_chart_display(self) -> None:
        """기존 데이터로 차트 마커만 재렌더링 (네트워크 호출 없음)"""
        chart_plot = self.query_one("#chart-plot", PlotextPlot)
        chart_plot.plt.clear_data()
        chart_plot.plt.clear_figure()
        if self.df is None or self.df.empty:
            chart_plot.plt.title(f"{self.ticker} 데이터를 사용할 수 없습니다")
        else:
            self._render_chart(chart_plot)
        chart_plot.refresh()

    async def on_context_updated(self, message: ContextUpdated) -> None:
        """컨텍스트 변경 시 거래 내역과 마커만 갱신 (데이터 재요청 없음)"""
        await self.refresh_trade_history()
        await self.refresh_chart_display()

    async def refresh_trade_history(self) -> None:
        container = self.query_one("#trade-history", VerticalScroll)
        await container.remove_children()

        # saved_context 보고서 + 캐시를 병합하여 거래 내역 구성 (파일은 사용하지 않음)
        trades_map: Dict[str, Dict[str, Any]] = {}

        # 우선순위: context < cache (나중에 들어온 것이 같은 날짜/시 키를 덮어씀)
        context_trades = _trades_from_context_reports(self.context, self.ticker)

        cache_portfolio = self.context.get_cache("portfolio", {}) or {}
        cache_trades = cache_portfolio.get(self.ticker, [])
        if isinstance(cache_trades, dict):
            cache_trades = [cache_trades]

        def _hour_key(dt_str: str) -> str:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:00", "%Y-%m-%d"):
                try:
                    return datetime.strptime(dt_str, fmt).strftime("%Y-%m-%d %H:00")
                except Exception:
                    continue
            return dt_str

        for source_trades in (context_trades, cache_trades):
            for t in source_trades or []:
                added_at = t.get("added_at")
                if not added_at:
                    continue
                trades_map[_hour_key(added_at)] = t

        trades = list(trades_map.values())

        if not trades:
            await container.mount(Static("거래 내역이 없습니다.", classes="trade-history-text"))
            return

        # 날짜 기준 내림차순 정렬 (최신순)
        sorted_trades = sorted(trades, key=lambda x: x.get("added_at", ""), reverse=True)

        for trade in sorted_trades:
            raw_datetime = trade.get("added_at", "") or ""
            # "unknown" 또는 빈 값 처리
            if not raw_datetime or raw_datetime.lower() == "unknown":
                trade_datetime = "날짜 없음"
            else:
                trade_datetime = raw_datetime
            decision = trade.get("decision", "") or "N/A"
            quantity = trade.get("quantity", "")

            # 시간 정보 포함하여 표시 (YYYY-MM-DD HH:MM:SS 형식)
            quantity_str = f" ({quantity}주)" if quantity else ""
            label = f"{trade_datetime} - {decision}{quantity_str}"

            # decision에 따른 색상 구분
            if "BUY" in decision.upper():
                variant = "success"
            elif "SELL" in decision.upper():
                variant = "error"
            else:
                variant = "primary"

            await container.mount(Static(label, classes="trade-history-text"))

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#refresh-button")
    def on_refresh_button_pressed(self) -> None:
        self.run_worker(self.load_stock_data())

    @on(Button.Pressed, ".step-button")
    def on_chart_type_button_pressed(self, event: Button.Pressed) -> None:
        """차트 타입 버튼 클릭 시 일봉/주봉/월봉 변경"""
        button_id = event.button.id or ""
        if button_id.startswith("chart-type-"):
            try:
                new_type = int(button_id.replace("chart-type-", ""))
                if 0 <= new_type < len(CHART_TYPE_OPTIONS):
                    self.current_chart_type = new_type
                    # 기본 표시 범위로 리셋
                    _, _, default_range = CHART_TYPE_OPTIONS[new_type]
                    self.display_range = default_range

                    # 버튼 활성화 상태 업데이트
                    for i in range(len(CHART_TYPE_OPTIONS)):
                        btn = self.query_one(f"#chart-type-{i}", Button)
                        if i == new_type:
                            btn.add_class("active")
                        else:
                            btn.remove_class("active")

                    # 새 차트 타입으로 데이터 재로드
                    self.run_worker(self.load_stock_data())
                    self._update_range_info()
            except (ValueError, Exception):
                pass

    @on(Button.Pressed, "#nav-left")
    def on_nav_left_pressed(self) -> None:
        """왼쪽 이동 (과거로)"""
        _, chart_type, _ = CHART_TYPE_OPTIONS[self.current_chart_type]
        step = STEP_UNITS[chart_type]
        if chart_type == "hourly":
            self.end_date = self.end_date - timedelta(hours=step)
        elif chart_type == "daily":
            self.end_date = self.end_date - timedelta(days=step)
        else:  # weekly
            self.end_date = self.end_date - timedelta(weeks=step)
        self._update_chart_and_info()

    @on(Button.Pressed, "#nav-right")
    def on_nav_right_pressed(self) -> None:
        """오른쪽 이동 (미래로)"""
        _, chart_type, _ = CHART_TYPE_OPTIONS[self.current_chart_type]
        step = STEP_UNITS[chart_type]
        if chart_type == "hourly":
            new_end = self.end_date + timedelta(hours=step)
        elif chart_type == "daily":
            new_end = self.end_date + timedelta(days=step)
        else:  # weekly
            new_end = self.end_date + timedelta(weeks=step)
        # 현재 날짜를 넘어가지 않도록 제한
        if new_end <= datetime.now():
            self.end_date = new_end
        else:
            self.end_date = datetime.now()
        self._update_chart_and_info()

    @on(Button.Pressed, "#zoom-out")
    def on_zoom_out_pressed(self) -> None:
        """확대 (범위 축소)"""
        _, chart_type, _ = CHART_TYPE_OPTIONS[self.current_chart_type]
        step = STEP_UNITS[chart_type]
        new_range = self.display_range - step
        if new_range >= step:  # 최소 범위는 단위 크기
            self.display_range = new_range
            self._update_chart_and_info()

    @on(Button.Pressed, "#zoom-in")
    def on_zoom_in_pressed(self) -> None:
        """축소 (범위 확대)"""
        _, chart_type, _ = CHART_TYPE_OPTIONS[self.current_chart_type]
        step = STEP_UNITS[chart_type]
        self.display_range = self.display_range + step
        self._update_chart_and_info()

    def _update_chart_and_info(self) -> None:
        """차트와 정보 업데이트"""
        self.run_worker(self.refresh_chart_display())
        # 헤더 정보 업데이트
        info = self.query_one("#chart-info", Static)
        info.update(f"Ticker: {self.ticker} | {self.end_date.strftime('%Y년 %m월 %d일')}")
        # 범위 정보 업데이트
        self._update_range_info()

    def _update_range_info(self) -> None:
        """범위 정보 라벨 업데이트"""
        range_info = self.query_one("#range-info", Static)
        range_info.update(self._get_range_label())

    def _get_range_label(self) -> str:
        """차트 타입에 맞는 범위 라벨 반환"""
        _, chart_type, _ = CHART_TYPE_OPTIONS[self.current_chart_type]
        if chart_type == "hourly":
            return f"{self.display_range}시간"
        elif chart_type == "daily":
            return f"{self.display_range}일"
        else:  # weekly
            return f"{self.display_range}주"

    @on(Button.Pressed, ".trade-history-item")
    def on_trade_history_item_pressed(self, event: Button.Pressed) -> None:
        # ID를 제거했으므로 라벨 기반으로 ticker/date 추출
        label = event.button.label or ""
        if " - " in label:
            try:
                trade_date_part, ticker_part = label.split(" - ", 1)
                ticker_part = ticker_part.split(" ", 1)[0].strip()  # "AAPL (SELL)" -> "AAPL"
                from cli.screens.trade_progress_screen import TradeProgressScreen
                self.app.push_screen(TradeProgressScreen(self.context, ticker_part, trade_date_part))
            except Exception:
                pass

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self.run_worker(self.load_stock_data())
