from pathlib import Path
from datetime import datetime
import json

from modules.graph.node import BaseNode
from graphs.trader.agents import RiskCheckerAgent, TraderAgent
from modules.context import Context

LOG_DIR = Path("logs/trader_decisions")
PORTFOLIO_FILE = Path("data/portfolio.json")

def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def _log_dir(context: Context) -> Path:
    tkr = context.get_cache("ticker", "UNKNOWN")
    dt = context.get_cache("trade_date", "UNKNOWN_DATE")
    return LOG_DIR / f"{tkr}_{dt}"

def _load_portfolio() -> dict:
    """포트폴리오 파일에서 불러오기"""
    if PORTFOLIO_FILE.exists():
        try:
            return json.loads(PORTFOLIO_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}

def _save_portfolio(portfolio: dict):
    """포트폴리오 파일에 저장"""
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    PORTFOLIO_FILE.write_text(
        json.dumps(portfolio, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


class RiskCheckerNode(BaseNode):
    def __init__(self, name: str = "RiskChecker"):
        super().__init__(name)
        self.agent = RiskCheckerAgent(name=f"{name}")

    def run(self, context: Context) -> Context:
        context = self.agent.run(context)
        self.state = 'passed'

        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            risk_assessment = context.get_cache("risk_assessment", {})
            _write_json(
                _log_dir(context) / f"risk_assessment_{ts}.json",
                {
                    "time": datetime.now().isoformat(),
                    "risk_assessment": risk_assessment,
                },
            )
        except Exception as e:
            print(f"[{self.name}][log]", e)

        risk_assessment = context.get_cache("risk_assessment", {})
        print(f"\n[{self.name}] Risk Assessment:")
        print(f"Risk Level: {risk_assessment.get('risk_level', 'N/A')}")
        print(f"Risk Score: {risk_assessment.get('risk_score', 'N/A')}/100")

        return context


class TraderNode(BaseNode):
    def __init__(self, name: str = "Trader"):
        super().__init__(name)
        self.agent = TraderAgent(name=f"{name}")

    def run(self, context: Context) -> Context:
        context = self.agent.run(context)
        self.state = 'passed'

        ticker = context.get_cache("ticker", "UNKNOWN")
        trade_date = context.get_cache("trade_date", "UNKNOWN_DATE")
        report_dir = context.get_cache("report_dir", "results")
        reports_dir = Path(report_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)

        trader_decision = context.get_cache("trader_decision", {})
        risk_assessment = context.get_cache("risk_assessment", {})

        decision = trader_decision.get("decision", "UNKNOWN")
        recommendation = trader_decision.get("recommendation", "No recommendation")
        confidence = trader_decision.get("confidence", 0)

        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            _write_json(
                _log_dir(context) / f"trader_decision_{ts}.json",
                {
                    "time": datetime.now().isoformat(),
                    "trader_decision": trader_decision,
                    "risk_assessment": risk_assessment,
                },
            )
        except Exception as e:
            print(f"[{self.name}][log]", e)

        md = [
            f"# Trading Decision for {ticker}",
            f"**Date**: {trade_date}",
            "",
            "## Final Decision",
            f"**{decision}** (Confidence: {confidence}%)",
            "",
            "## Recommendation",
            recommendation,
            "",
            "## Risk Assessment",
            f"- **Risk Level**: {risk_assessment.get('risk_level', 'N/A')}",
            f"- **Risk Score**: {risk_assessment.get('risk_score', 'N/A')}/100",
            f"- **Risk Factors**: {risk_assessment.get('risk_factors', 'N/A')}",
        ]

        trader_decision_content = "\n".join(md)
        (reports_dir / "trader_decision.md").write_text(trader_decision_content, encoding="utf-8")

        print(f"\n[{self.name}] Trading Decision:")
        print(f"Decision: {decision} (Confidence: {confidence}%)")
        print(f"Recommendation: {recommendation}")

        # 테스트 모드 확인
        test_mode = context.get_config("test_mode_force_buy", False)
        original_decision = decision
        if test_mode and decision == "HOLD":
            decision = "BUY"
            print(f"\n[{self.name}] [TEST MODE] Converting HOLD to BUY for testing")
            print(f"[{self.name}] Original Decision: {original_decision} → Forced: {decision}")

        # 주문 실행 로직
        kis_trader = context.get_cache("kis_trader")
        if decision in ["BUY", "SELL"]:
            if kis_trader:
                # AI가 계산한 수량 사용
                ai_quantity = trader_decision.get("quantity", 1)
                config_quantity = context.get_config("order_quantity", 1)
                quantity = ai_quantity if ai_quantity and ai_quantity > 0 else config_quantity
                price = context.get_config("order_price", 0)

                print(f"\n[{self.name}] Order Request:")
                print(f"  - Ticker: {ticker}")
                print(f"  - Decision: {decision}")
                print(f"  - Quantity: {quantity} shares (AI calculated: {ai_quantity})")
                print(f"  - Price: {'Market' if price == 0 else f'${price}'}")
                print(f"\n[{self.name}] Executing order via KIS API...")

                try:
                    order_result = kis_trader.order_overseas(
                        stock_no=ticker,
                        qty=quantity,
                        order_type=decision,
                        exchange="NASD",
                        price=float(price)
                    )
                    context.set_cache(kis_order_result=order_result)

                    # 결과 로깅
                    order_success = False
                    if order_result and order_result.get('status_code') == 200:
                        response = order_result.get('response', {})
                        rt_cd = response.get('rt_cd', 'N/A')
                        if rt_cd == '0':
                            print(f"[{self.name}] [SUCCESS] Order completed")
                            order_success = True
                        else:
                            print(f"[{self.name}] [FAILED] Order failed: {response.get('msg1', 'Unknown error')}")
                    else:
                        print(f"[{self.name}] [ERROR] HTTP Error: {order_result.get('status_code')}")

                    # Portfolio 업데이트 (성공한 경우만)
                    if order_success:
                        # 파일에서 포트폴리오 불러오기
                        portfolio = _load_portfolio()

                        # 거래 히스토리 추가
                        trade_record = {
                            'added_at': context.get_cache('date', 'UNKNOWN'),
                            'decision': decision,
                            'quantity': quantity,
                            'confidence': trader_decision.get('confidence', 50),
                            'order_no': order_result.get('response', {}).get('output', {}).get('ODNO', 'N/A'),
                        }

                        if ticker not in portfolio:
                            portfolio[ticker] = []

                        portfolio[ticker].append(trade_record)

                        # 파일에 저장
                        _save_portfolio(portfolio)

                        # 로깅
                        if decision == "BUY":
                            print(f"[{self.name}] Portfolio Updated: {ticker} (+{quantity} shares, BUY)")
                        elif decision == "SELL":
                            print(f"[{self.name}] Portfolio Updated: {ticker} (-{quantity} shares, SELL)")
                        else:
                            print(f"[{self.name}] Portfolio Updated: {ticker} (HOLD)")

                        # 메모리에도 캐시 (선택사항)
                        context.set_cache(portfolio=portfolio)

                except Exception as e:
                    print(f"[{self.name}] [ERROR] Order execution error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"\n[{self.name}] [WARNING] KIS Trader not initialized - Order NOT executed")
        else:
            print(f"\n[{self.name}] [INFO] Decision is {decision} - No order execution")

        return context
