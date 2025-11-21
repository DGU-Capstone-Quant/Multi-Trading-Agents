from graphs.rank import create_rank_graph
from graphs.trader.factory import create_trader_graph
from modules.kis_trader import RealTrader
from graphs.trader import nodes as trader_nodes
from modules.context import Context

# 설정
APP_KEY = "" # PS4zRGLHMEMJnPlKbfMAc5sHRE3Ou082JC67
APP_SECRET = "" # PC8ZHFBwvWaKdXqfRhSPGBWtuPuqqSU9pxWzqRVexSWD4EJc4iZ9R3fRDJ4zQZjb4geIaOBzjygQg4evhfdmWY8aac2wSwwBOkb5KWlx3LmeXtpsrDUohFtUwL4hHPiGHPZ4i72UblMDYRz5WtnsbTC31teQkPzNrqqBkAHnOZZ3xrojgQ4=
RAPID_API_KEY = ""
ACCOUNT_NO = "" # 50156991
IS_MOCK = True
TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
ANALYSIS_TASKS = ["financial"]
MAX_PORTFOLIO_SIZE = 3
ORDER_QUANTITY = 1  # AI 계산 실패시 fallback
ORDER_PRICE = 0  # 0: 시장가
TEST_MODE_FORCE_BUY = False


def validate_config():
    if not APP_KEY or not APP_SECRET:
        raise ValueError("[ERROR] API 키가 설정되지 않았습니다.")

    if not IS_MOCK:
        print("\n" + "="*60)
        print("[경고] 실전투자 모드입니다!")
        print("="*60)
        confirm = input("실제 계좌에서 거래를 진행하시겠습니까? (yes/no): ")
        if confirm.lower() != "yes":
            raise ValueError("사용자가 실전투자를 취소했습니다.")


def main():
    global APP_KEY, APP_SECRET, ACCOUNT_NO, RAPID_API_KEY
    import os

    print("="*60)
    print("AI 자동 거래 시스템")
    print("="*60)

    if not APP_KEY:
        print("\n[API 키 입력]")
        APP_KEY = input("KIS_APP_KEY: ").strip()

    if not APP_SECRET:
        APP_SECRET = input("KIS_APP_SECRET: ").strip()

    if not RAPID_API_KEY:
        RAPID_API_KEY = input("RAPID_API_KEY: ").strip()
        os.environ["RAPID_API_KEY"] = RAPID_API_KEY

    if not ACCOUNT_NO:
        ACCOUNT_NO = input("계좌번호 (예: 50156991): ").strip()

    try:
        validate_config()
    except ValueError as e:
        print(f"\n{e}")
        return

    print(f"\n[설정 정보]")
    print(f"  - 모드: {'모의투자' if IS_MOCK else '실전투자'}")
    print(f"  - 계좌번호: {ACCOUNT_NO}")
    print(f"  - 분석 종목: {', '.join(TICKERS)}")
    print(f"  - 최대 포트폴리오: {MAX_PORTFOLIO_SIZE}개")
    print(f"  - 주문 수량: {ORDER_QUANTITY}주")
    print(f"  - 주문 가격: {'시장가' if ORDER_PRICE == 0 else f'{ORDER_PRICE}원'}")

    print(f"\n[KIS API 초기화 중...]")
    try:
        if "-" in ACCOUNT_NO:
            cano, acnt_prdt_cd = ACCOUNT_NO.split("-")
        else:
            cano = ACCOUNT_NO
            acnt_prdt_cd = "01"

        kis_trader = RealTrader(
            app_key=APP_KEY,
            app_secret=APP_SECRET,
            cano=cano,
            acnt_prdt_cd=acnt_prdt_cd,
            is_mock=IS_MOCK
        )
        trader_nodes.kis_trader = kis_trader
        print("[OK] KIS API 초기화 완료")
    except Exception as e:
        print(f"[ERROR] KIS API 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    context = Context()
    context.set_config(
        analysis_tasks=ANALYSIS_TASKS,
        tickers=TICKERS,
        max_portfolio_size=MAX_PORTFOLIO_SIZE,
        order_quantity=ORDER_QUANTITY,
        order_price=ORDER_PRICE,
        test_mode_force_buy=TEST_MODE_FORCE_BUY,
    )

    from datetime import datetime
    current_date = datetime.now().strftime("%Y%m%dT%H%M")
    context.set_cache(
        date=current_date,
        trade_date=current_date
    )

    print("\n" + "="*60)
    print("Step 1: 종목 분석 및 순위 선정")
    print("="*60)

    try:
        rank_graph = create_rank_graph()
        context = rank_graph.run(context)
        print("\n[OK] 종목 분석 완료")
    except Exception as e:
        print(f"\n[ERROR] 종목 분석 실패: {e}")
        return

    recommendations = context.get_cache("recommendation", [])
    if not recommendations:
        print("\n[경고] 추천 종목이 없습니다. 거래를 종료합니다.")
        return

    print(f"\n[추천 종목] {', '.join(recommendations)}")

    print("\n" + "="*60)
    print("Step 2: 종목 분석 및 투자 계획 수립")
    print("="*60)

    try:
        from graphs.debate.factory import create_debate_graph
        debate_graph = create_debate_graph()
        context.set_cache(tickers=recommendations)
        context.set_config(rounds=2)
        context = debate_graph.run(context)
        print("\n[OK] 투자 계획 수립 완료")
    except Exception as e:
        print(f"\n[ERROR] 투자 계획 수립 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "="*60)
    print("Step 3: 거래 결정 및 실행")
    print("="*60)

    try:
        trader_graph = create_trader_graph()
        context.set_cache(tickers=recommendations)
        context = trader_graph.run(context)
        print("\n[OK] 거래 실행 완료")
    except Exception as e:
        print(f"\n[ERROR] 거래 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "="*60)
    print("거래 결과 요약")
    print("="*60)

    kis_order_result = context.get_cache("kis_order_result")
    if kis_order_result:
        print(f"\n[주문 결과]")
        print(f"  - 상태: {kis_order_result.get('status_code')}")
        print(f"  - 종목: {kis_order_result.get('stock_no')}")
        print(f"  - 타입: {kis_order_result.get('order_type')}")
        print(f"  - 수량: {kis_order_result.get('qty')}주")
        price_val = kis_order_result.get('price', 0)
        print(f"  - 가격: {'시장가' if price_val == 0 else f'${price_val}'}")

        response = kis_order_result.get('response', {})
        if isinstance(response, dict):
            print(f"  - 응답: {response.get('rt_cd', 'N/A')} - {response.get('msg1', 'N/A')}")
            output = response.get('output', {})
            if output and 'ODNO' in output:
                print(f"  - 주문번호: {output['ODNO']} ✅")
    else:
        print("\n주문 없음 (HOLD 또는 오류)")

    if kis_order_result and kis_trader:
        print(f"\n[거래 후 계좌 확인]")
        try:
            kis_trader.get_overseas_balance()
            kis_trader.get_overseas_cash()
        except Exception as e:
            print(f"  - 조회 실패: {e}")

    print("\n" + "="*60)
    print("완료")
    print("="*60)


if __name__ == "__main__":
    main()
