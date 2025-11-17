"""results 폴더 데이터 로드 유틸리티"""

from pathlib import Path
from typing import List, Dict

from modules.context import Context


def load_results_to_context(context: Context, results_dir: str = "results") -> None:
    """
    results 폴더의 모든 보고서 데이터를 Context로 로드
    """
    results_path = Path(results_dir)

    if not results_path.exists():
        return

    portfolio = set()
    completed_debates = []

    for ticker_dir in results_path.iterdir():
        if not ticker_dir.is_dir():
            continue

        ticker = ticker_dir.name

        for date_dir in ticker_dir.iterdir():
            if not date_dir.is_dir():
                continue

            trade_date = date_dir.name
            reports_dir = date_dir / "reports"

            if not reports_dir.exists():
                continue

            completed_debates.append({"ticker": ticker, "trade_date": trade_date})

            # 보고서 파일 로드
            _load_report_file(context, reports_dir / "market_report.md", ticker, trade_date, "market_report")
            _load_report_file(context, reports_dir / "investment_plan.md", ticker, trade_date, "investment_plan")
            _load_report_file(context, reports_dir / "trader_decision.md", ticker, trade_date, "trader_decision")

        if any(date_dir.is_dir() for date_dir in ticker_dir.iterdir()):
            portfolio.add(ticker)

    context.set_cache(
        portfolio=sorted(list(portfolio)),
        completed_debates=completed_debates
    )


def _load_report_file(
    context: Context,
    file_path: Path,
    ticker: str,
    trade_date: str,
    report_type: str
) -> None:
    """보고서 파일을 읽어 Context에 저장"""
    if not file_path.exists():
        return

    try:
        content = file_path.read_text(encoding="utf-8")
        key = f"{ticker}_{trade_date}_{report_type}"
        context.set_report(key, content)
    except Exception:
        pass


def scan_date_ticker_map(results_dir: str = "results") -> Dict[str, List[str]]:
    """
    results 폴더를 스캔하여 trade_date별 ticker 매핑 반환
    """
    results_path = Path(results_dir)

    if not results_path.exists():
        return {}

    date_ticker_map = {}

    for ticker_dir in results_path.iterdir():
        if not ticker_dir.is_dir():
            continue

        ticker = ticker_dir.name

        for date_dir in ticker_dir.iterdir():
            if not date_dir.is_dir():
                continue

            trade_date = date_dir.name

            if trade_date not in date_ticker_map:
                date_ticker_map[trade_date] = []

            date_ticker_map[trade_date].append(ticker)

    # trade_date 순서대로 정렬
    sorted_dates = sorted(date_ticker_map.keys())
    return {trade_date: sorted(date_ticker_map[trade_date]) for trade_date in sorted_dates}
