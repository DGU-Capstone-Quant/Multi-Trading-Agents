#!/usr/bin/env python3
# Textual 기반 주식 데이터 시각화 CLI 도구

# TUI 애플리케이션 개발용
from textual.app import App, ComposeResult
# UI 레이아웃 구성용
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
# UI 구성 요소들
from textual.widgets import Header, Footer, Static, Button, Input, Label, OptionList
from textual.widgets.option_list import Option
# 값 변경 시 자동 업데이트
from textual.reactive import reactive
# 스크린 관리
from textual.screen import ModalScreen
# 이벤트 핸들러 등록
from textual import on
# 터미널에서 그래프를 그리는 위젯
from textual_plotext import PlotextPlot
# pandas를 이용한 데이터 처리
import pandas as pd
# 주식 데이터 가져오는 함수
from modules.utils.fetch import (
    fetch_time_series_intraday,  # 일중 데이터
    fetch_time_series_daily,     # 일간 데이터
    fetch_time_series_weekly,    # 주간 데이터
    fetch_time_series_monthly    # 월간 데이터
)


class CommandPalette(ModalScreen): # 명령어 팔레트 팝업
    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    CSS = """
    CommandPalette {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #command-dialog {
        width: 80;
        height: auto;
        max-height: 35;
        background: $boost;
        border: heavy $accent;
        padding: 2 3;
    }

    #command-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        background: $panel;
        padding: 1;
    }

    OptionList {
        height: 20;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }

    OptionList > .option-list--option {
        padding: 0 2;
    }

    OptionList > .option-list--option-highlighted {
        background: $accent;
        color: $text;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="command-dialog"):
            yield Static("명령어 목록", id="command-title")
            yield OptionList(
                Option("q          프로그램 종료", id="cmd-quit"),
                Option("r          현재 데이터 새로고침", id="cmd-refresh"),
                Option("h          명령어 도움말 열기/닫기", id="cmd-palette"),
                Option("Tab        다음 입력 필드로 이동", id="cmd-tab"),
                Option("Shift+Tab  이전 입력 필드로 이동", id="cmd-shift-tab"),
                Option("Enter      데이터 가져오기", id="cmd-enter"),
                Option("Escape     이 창 닫기", id="cmd-escape"),
            )

    @on(OptionList.OptionSelected)
    def option_selected(self, event: OptionList.OptionSelected) -> None:
        """옵션이 선택되었을 때 팝업 닫기"""
        self.dismiss()


class StockChart(Static): # 주식 차트를 표시하는 위젯 클래스
    # 값이 변경되면 watch_data 메서드 자동 호출
    data = reactive(None, always_update=True)
    # 차트 제목
    title = reactive("")
    # 차트 타입
    chart_type = reactive("close")

    def __init__(self, title: str = "", chart_type: str = "close", *args, **kwargs):
        # 부모 클래스 초기화
        super().__init__(*args, **kwargs)
        self.title = title
        self.chart_type = chart_type
        # 차트 렌더링용 PlotextPlot 인스턴스 생성
        self.plt = PlotextPlot()

    def compose(self) -> ComposeResult:
        # PlotextPlot을 위젯으로 추가
        yield self.plt

    def watch_data(self, data: pd.DataFrame) -> None: # data 속성이 변경될 때 자동 호출
        # 데이터가 None이거나 비어있으면 종료
        if data is None:
            return
        if isinstance(data, pd.DataFrame) and data.empty:
            return

        # 차트 업데이트
        self.update_chart(data)

    def update_chart(self, data: pd.DataFrame) -> None: # 데이터로 차트를 렌더링
        # plotext 객체 가져오기
        plt = self.plt.plt
        # 이전 데이터 제거
        plt.clear_data()
        # 차트 전체 초기화
        plt.clear_figure()

        # 데이터가 비어있으면 메시지 표시 후 종료
        if isinstance(data, pd.DataFrame) and data.empty:
            plt.title("No data available")
            self.plt.refresh()
            return
        elif not isinstance(data, pd.DataFrame):
            plt.title("Invalid data type")
            self.plt.refresh()
            return

        # timestamp 기준 데이터 정렬
        data = data.sort_values('timestamp')

        # x축 레이블 생성
        x_labels = data['timestamp'].dt.strftime('%Y-%m-%d %H:%M').tolist()
        # x축 좌표 생성
        x = list(range(len(data)))

        # 차트 타입에 따라 다른 그래프 그리기
        if self.chart_type == "close":
            # 종가 차트
            y = data['close'].tolist()
            plt.plot(x, y, label="Close Price", marker="braille")
            plt.title(f"{self.title} - Close Price")
        elif self.chart_type == "ohlc":
            # OHLC(시가/고가/저가/종가) 차트
            plt.plot(x, data['open'].tolist(), label="Open", marker="braille")
            plt.plot(x, data['high'].tolist(), label="High", marker="braille")
            plt.plot(x, data['low'].tolist(), label="Low", marker="braille")
            plt.plot(x, data['close'].tolist(), label="Close", marker="braille")
            plt.title(f"{self.title} - OHLC")
        elif self.chart_type == "volume":
            # 거래량 막대 차트
            y = data['volume'].tolist()
            plt.bar(x, y, label="Volume")
            plt.title(f"{self.title} - Volume")

        # x축 레이블을 10개 정도만 표시 (겹침 방지)
        step = max(1, len(x_labels) // 10)
        plt.xticks([x[i] for i in range(0, len(x), step)],
                   [x_labels[i] for i in range(0, len(x_labels), step)])

        # x축, y축 레이블 설정
        plt.xlabel("Date")
        plt.ylabel("Price" if self.chart_type != "volume" else "Volume")

        # 차트 화면에 표시
        self.plt.refresh()


class StockVisualizerApp(App): # 주식 데이터 시각화
    CSS = """
    Screen {
        layout: vertical;
        background: $surface;
    }

    #input-container {
        layout: horizontal;
        height: auto;
        padding: 1 2;
        background: $boost;
        border: heavy $primary;
        margin: 1;
    }

    #charts-scroll {
        height: 1fr;
        margin: 0 1 1 1;
    }

    .chart-container {
        height: 20;
        padding: 1 2;
        background: $panel;
        border: tall $accent;
        margin-bottom: 1;
    }

    Input {
        width: 12;
        margin-right: 1;
        border: solid $accent;
        background: $surface;
    }

    #ticker-input {
        width: 12;
    }

    #date-from-input, #date-to-input {
        width: 16;
    }

    Input:focus {
        border: solid $success;
    }

    Button {
        margin-right: 1;
        min-width: 14;
        border: solid $accent;
    }

    Button:hover {
        background: $accent;
        border: solid $accent-darken-1;
    }

    Button:focus {
        text-style: bold;
    }

    Label {
        padding-right: 1;
        content-align: center middle;
        text-style: bold;
        color: $text;
        min-width: 8;
    }

    StockChart {
        border: none;
        background: $panel;
    }
    """

    # 키보드 단축키 바인딩
    BINDINGS = [
        ("q", "quit", "Quit"),              # q 키를 누르면 종료
        ("r", "refresh", "Refresh"),        # r 키를 누르면 새로고침
        ("h", "command_palette", "Help"),   # h 키로 명령어 팔레트 열기
    ]

    def __init__(self):
        # 부모 클래스 초기화
        super().__init__()
        self.current_ticker = None

    def compose(self) -> ComposeResult: # UI 레이아웃을 구성하는 메서드
        # 헤더 추가
        yield Header()

        # 티커 심볼 입력
        with Container(id="input-container"):
            # 티커 레이블
            yield Label("Ticker:")
            # 티커 입력 필드
            yield Input(placeholder="티커 심볼", id="ticker-input", value="AAPL")
            # 시작 날짜 레이블
            yield Label("From:")
            # 시작 날짜 입력 필드
            yield Input(placeholder="YYYYMMDD", id="date-from-input", value="")
            # 종료 날짜 레이블
            yield Label("To:")
            # 종료 날짜 입력 필드
            yield Input(placeholder="YYYYMMDD", id="date-to-input", value="")
            # 데이터 가져오기 버튼
            yield Button("Fetch All Data", id="fetch-button", variant="primary")

        # 차트들이 표시되는 스크롤 영역
        with VerticalScroll(id="charts-scroll"):
            # 5분 간격 차트
            with Container(classes="chart-container"):
                yield StockChart(title="5 Min Interval", chart_type="close", id="chart-5min")

            # 일간 차트
            with Container(classes="chart-container"):
                yield StockChart(title="Daily", chart_type="close", id="chart-daily")

            # 주간 차트
            with Container(classes="chart-container"):
                yield StockChart(title="Weekly", chart_type="close", id="chart-weekly")

            # 월간 차트
            with Container(classes="chart-container"):
                yield StockChart(title="Monthly", chart_type="close", id="chart-monthly")

            # 일간 OHLC 차트
            with Container(classes="chart-container"):
                yield StockChart(title="Daily OHLC", chart_type="ohlc", id="chart-daily-ohlc")

            # 일간 거래량 차트
            with Container(classes="chart-container"):
                yield StockChart(title="Daily Volume", chart_type="volume", id="chart-daily-volume")

        # 푸터 추가
        yield Footer()

    @on(Button.Pressed, "#fetch-button")
    async def fetch_stock_data(self) -> None: # Fetch Data 버튼이 눌렸을 때 호출되는 메서드
        # UI 요소들 가져오기
        ticker_input = self.query_one("#ticker-input", Input)
        date_from_input = self.query_one("#date-from-input", Input)
        date_to_input = self.query_one("#date-to-input", Input)

        # 티커 심볼 가져오기
        ticker = ticker_input.value.strip().upper()
        date_from = date_from_input.value.strip()
        date_to = date_to_input.value.strip()

        if not ticker:
            self.notify("티커 심볼을 입력하세요.", severity="warning")
            return

        # 현재 티커 저장
        self.current_ticker = ticker

        # 데이터 로딩 시작 알림
        period_msg = ""
        if date_from or date_to:
            period_msg = f" ({date_from or 'all'} ~ {date_to or 'now'})"
        self.notify(f"{ticker}{period_msg} 데이터를 가져오는 중...", severity="information")

        try:
            # 5분 간격 데이터 가져오기 (날짜별 조회는 date 파라미터 사용)
            self.notify("5분 간격 데이터 로딩 중...", severity="information")
            if date_from and len(date_from) == 8:
                # 특정 날짜 지정
                data_5min = fetch_time_series_intraday(ticker=ticker, interval="5min", date=date_from)
            else:
                # 전체 데이터
                data_5min = fetch_time_series_intraday(ticker=ticker, interval="5min")
            chart_5min = self.query_one("#chart-5min", StockChart)
            chart_5min.data = data_5min

            # 일간 데이터 가져오기
            self.notify("일간 데이터 로딩 중...", severity="information")
            data_daily = fetch_time_series_daily(ticker=ticker, date_from=date_from, date_to=date_to)
            chart_daily = self.query_one("#chart-daily", StockChart)
            chart_daily.data = data_daily

            chart_daily_ohlc = self.query_one("#chart-daily-ohlc", StockChart)
            chart_daily_ohlc.data = data_daily

            chart_daily_volume = self.query_one("#chart-daily-volume", StockChart)
            chart_daily_volume.data = data_daily

            # 주간 데이터 가져오기
            self.notify("주간 데이터 로딩 중...", severity="information")
            data_weekly = fetch_time_series_weekly(ticker=ticker, date_from=date_from, date_to=date_to)
            chart_weekly = self.query_one("#chart-weekly", StockChart)
            chart_weekly.data = data_weekly

            # 월간 데이터 가져오기
            self.notify("월간 데이터 로딩 중...", severity="information")
            data_monthly = fetch_time_series_monthly(ticker=ticker, date_from=date_from, date_to=date_to)
            chart_monthly = self.query_one("#chart-monthly", StockChart)
            chart_monthly.data = data_monthly

            self.notify(f"{ticker} 모든 데이터 로딩 완료!", severity="success")

        except Exception as e:
            self.notify(f"에러: {str(e)}", severity="error")

    def action_refresh(self) -> None: # r키를 누를 시 새로고침
        if self.current_ticker:
            self.notify(f"{self.current_ticker} 데이터를 다시 가져옵니다...", severity="information")
            self.fetch_stock_data()

    def action_command_palette(self) -> None: # h 키로 명령어 팔레트 열기
        """명령어 팔레트 모달 표시"""
        self.push_screen(CommandPalette())


def main():
    app = StockVisualizerApp()
    app.run()


if __name__ == "__main__":
    main()
