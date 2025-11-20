"""주가 차트 화면"""

import plotext as plt
from datetime import datetime, timedelta
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Container, Horizontal, VerticalScroll
from textual import on
from textual_plotext import PlotextPlot

from modules.context import Context
from modules.utils.fetch import fetch_time_series_daily
from cli.base import BaseScreen
from cli.events import ContextUpdated
from cli.screens.utils import build_trade_label, trader_decision_key, trader_recommendation_key


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
    """

    BINDINGS = [("escape", "back", "뒤로 가기"), ("r", "refresh", "새로고침")]

    def __init__(self, context: Context, ticker: str, *args, **kwargs):
        super().__init__(context, *args, **kwargs)
        self.ticker = ticker
        self.df = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="chart-container"):
            with Container(id="chart-header"):
                yield Static(f"{self.ticker} 주가 차트", id="chart-title")
                yield Static(f"Ticker: {self.ticker}", id="chart-info")
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
        try:
            now = datetime.now()
            # 최근 1년치만 가져와 차트와 마커 계산에 사용
            self.df = fetch_time_series_daily(
                ticker=self.ticker,
                days=365,
                date_to=now.strftime("%Y-%m-%d"),
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
        # 최근 1년치 전체(최대 fetch 범위)에서 렌더링
        df_chart = self.df.copy().sort_values('timestamp')
        dates = df_chart['timestamp'].dt.strftime('%Y-%m-%d').tolist()
        close_prices = df_chart['close'].tolist()

        x = list(range(len(df_chart)))

        chart_plot.plt.plot(x, close_prices, marker="braille")

        buy_points_x, buy_points_y, sell_points_x, sell_points_y = [], [], [], []
        hold_points_x, hold_points_y = [], []

        # 모든 거래 이벤트 수집 (진행중 + 완료)
        trade_events = []
        seen_dates = set()
        for key in self.context.get_cache("trade_progress_keys", []):
            data = self.context.get_cache(key, {}) or {}
            if data.get("ticker") == self.ticker and data.get("trade_date"):
                seen_dates.add(data["trade_date"])
                trade_events.append(data["trade_date"])
        for debate in self.context.get_cache("completed_debates", []):
            if debate.get("ticker") == self.ticker and debate.get("trade_date") and debate["trade_date"] not in seen_dates:
                trade_events.append(debate["trade_date"])

        for trade_date in trade_events:
            # 차트에 없는 날짜면 가장 가까운 날짜로 매핑
            if trade_date in dates:
                idx = dates.index(trade_date)
            else:
                try:
                    target = datetime.strptime(trade_date, "%Y-%m-%d")
                    idx = min(range(len(dates)), key=lambda i: abs(datetime.strptime(dates[i], "%Y-%m-%d") - target))
                except Exception:
                    continue

            decision = self.context.get_cache(trader_decision_key(self.ticker, trade_date), "").upper()
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

        chart_plot.plt.title(f"{self.ticker} 주가 (최근 1년)  |  BUY:^(green)  SELL:v(red)  HOLD:•(yellow)")
        chart_plot.plt.xlabel("날짜")
        chart_plot.plt.ylabel("가격 ($)")
        step = max(1, len(x) // 12)
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
        entries = self._collect_trade_history_entries()
        if not entries:
            await container.mount(Static("거래 내역이 없습니다.", classes="trade-history-text"))
        for entry in entries:
            await container.mount(Button(build_trade_label(entry), id=None, classes="trade-history-item", variant="warning" if entry["is_active"] else "primary"))

    def _collect_trade_history_entries(self) -> list:
        entries, seen = [], set()

        for key in self.context.get_cache("trade_progress_keys", []):
            data = self.context.get_cache(key, {})
            if data.get("ticker") == self.ticker:
                seen.add(f"{data['ticker']}_{data['trade_date']}")
                ticker, trade_date = data["ticker"], data["trade_date"]
                entries.append({
                    "ticker": ticker, "trade_date": trade_date, "status": data.get("status", "completed"),
                    "decision": self.context.get_cache(trader_decision_key(ticker, trade_date), ""),
                    "recommendation": self.context.get_cache(trader_recommendation_key(ticker, trade_date), ""),
                    "is_active": data.get("status") != "completed"
                })

        for debate in self.context.get_cache("completed_debates", []):
            if debate.get("ticker") == self.ticker and f"{debate['ticker']}_{debate['trade_date']}" not in seen:
                ticker, trade_date = debate["ticker"], debate["trade_date"]
                entries.append({
                    "ticker": ticker, "trade_date": trade_date, "status": debate.get("status", "completed"),
                    "decision": self.context.get_cache(trader_decision_key(ticker, trade_date), ""),
                    "recommendation": self.context.get_cache(trader_recommendation_key(ticker, trade_date), ""),
                    "is_active": False
                })

        entries.sort(key=lambda x: (x["is_active"], x["trade_date"]), reverse=True)
        return entries[:10]

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#refresh-button")
    def on_refresh_button_pressed(self) -> None:
        self.run_worker(self.load_stock_data())

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
