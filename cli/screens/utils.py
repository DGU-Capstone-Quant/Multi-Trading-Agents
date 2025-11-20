"""화면 공통 유틸리티 함수"""

from typing import Dict
from datetime import datetime


def make_progress_key(ticker: str, trade_date: str) -> str:
    """거래 진행 상황 캐시 키 생성"""
    return f"trade_progress_{ticker}_{trade_date}"


def trader_decision_key(ticker: str, trade_date: str) -> str:
    return f"{ticker}_{trade_date}_trader_decision"


def trader_recommendation_key(ticker: str, trade_date: str) -> str:
    return f"{ticker}_{trade_date}_trader_recommendation"


def format_time(seconds: int) -> str:
    """초를 시:분:초 형식으로 변환"""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours > 0 else f"{minutes:02d}:{secs:02d}"


def _normalize_report_date(trade_date: str) -> str:
    """그래프 포맷(YYYYMMDDTHHMM)으로 변환."""
    if not trade_date:
        return trade_date
    for fmt in ("%Y%m%dT%H%M", "%Y%m%dT%H", "%Y-%m-%d"):
        try:
            return datetime.strptime(trade_date, fmt).strftime("%Y%m%dT%H%M")
        except ValueError:
            continue
    return trade_date


def _format_report_dict(report: dict) -> str:
    return (
        report.get("title", "")
        + "\n\nKey Considerations:\n"
        + report.get("key_considerations", "")
        + "\n\nIndicators Table:\n"
        + report.get("indicators_table", "")
        + "\n\nDetailed Analysis:\n"
        + report.get("detailed_analysis", "")
        + "\n\nConclusion:\n"
        + report.get("conclusion", "")
        + "\n\nRecommendation:\n"
        + report.get("recommendation", "")
    )


def _get_report_text(context, ticker: str, normalized_date: str, task: str) -> str:
    try:
        return context.get_report(ticker, normalized_date, task)
    except Exception:
        pass

    try:
        cache_key = datetime.strptime(normalized_date, "%Y%m%dT%H%M").strftime("%Y%m%dT%H")
    except ValueError:
        cache_key = normalized_date

    report_obj = getattr(context, "reports", {}).get(ticker, {}).get(cache_key, {}).get(task)
    if isinstance(report_obj, dict):
        return _format_report_dict(report_obj)
    if isinstance(report_obj, str):
        return report_obj
    return ""


def get_report_from_context(context, ticker: str, trade_date: str, report_type: str) -> str:
    """Context에서 보고서 가져오기 (공통 로직)"""
    if report_type == "investment_plan":
        normalized_date = _normalize_report_date(trade_date)
        content = _get_report_text(context, ticker, normalized_date, "investment_plan")
        if not content:
            legacy_key = f"{ticker}_{trade_date}_investment_plan"
            content = context.get_cache(legacy_key, "")
        return content or f"투자 계획 보고서를 찾을 수 없습니다.\n(ticker: {ticker}, date: {trade_date})"

    if report_type == "trader_decision":
        decision_key = trader_decision_key(ticker, trade_date)
        recommendation_key = trader_recommendation_key(ticker, trade_date)
        decision = context.get_cache(decision_key, "")
        recommendation = context.get_cache(recommendation_key, "")

        if not decision and not recommendation:
            return f"트레이더 결정 보고서를 찾을 수 없습니다."

        return f"**결정:**\n{decision}\n\n**추천:**\n{recommendation}"

    if report_type == "market_report":
        # analyst가 financial로 생성하므로 financial로 조회
        normalized_date = _normalize_report_date(trade_date)
        content = _get_report_text(context, ticker, normalized_date, "financial")
        return content or f"시장 분석 보고서를 찾을 수 없습니다.\n(ticker: {ticker}, date: {trade_date})"

    # 기타 보고서
    normalized_date = _normalize_report_date(trade_date)
    content = _get_report_text(context, ticker, normalized_date, report_type)
    if not content:
        key = f"{ticker}_{trade_date}_{report_type}"
        content = context.get_cache(key, "")
    return content or f"[{report_type}] 보고서를 찾을 수 없습니다."


def format_status_text(status: str) -> str:
    """상태 텍스트 포맷"""
    status_map = {
        "debate_in_progress": "상태: 토론 진행 중",
        "plan_ready": "상태: 토론 완료 - 트레이더 검토 중",
        "completed": "상태: 거래 완료",
    }
    return status_map.get(status, "상태: 준비 중")


def build_trade_label(entry: Dict) -> str:
    """거래 내역 라벨 생성"""
    status = entry.get("status", "")
    status_labels = {
        "plan_ready": "트레이더 검토 중",
        "debate_in_progress": "토론 진행 중",
        "completed": entry.get("decision") or "거래 완료",
    }
    status_label = status_labels.get(status, "진행 중")
    return f"{entry['trade_date']} - {entry['ticker']} ({status_label})"
