from graphs.main.graph import create_main_graph
from graphs.trader.factory import create_trader_graph
from modules.kis_trader import RealTrader
from modules.context import Context
from datetime import datetime
import os

# API 키 입력
APP_KEY = input("KIS_APP_KEY: ").strip()
APP_SECRET = input("KIS_APP_SECRET: ").strip()
RAPID_API_KEY = input("RAPID_API_KEY: ").strip()
ACCOUNT_NO = input("계좌번호 (예: 50156991-01): ").strip()

os.environ["RAPID_API_KEY"] = RAPID_API_KEY

# 계좌번호 파싱
cano, acnt_prdt_cd = ACCOUNT_NO.split("-") if "-" in ACCOUNT_NO else (ACCOUNT_NO, "01")

# KIS Trader 초기화 (모의투자 고정)
kis_trader = RealTrader(app_key=APP_KEY, app_secret=APP_SECRET, cano=cano, acnt_prdt_cd=acnt_prdt_cd, is_mock=True)

# Context 초기화
context = Context()
context.set_cache(date=datetime.now().strftime("%Y%m%dT%H%M"), trade_date=datetime.now().strftime("%Y%m%dT%H%M"), kis_trader=kis_trader)
context.set_config(analysis_tasks=["financial"], tickers=["AAPL", "GOOGL", "MSFT"], max_portfolio_size=3, order_quantity=1, order_price=0, test_mode_force_buy=True, rounds=2)

# Main Graph 실행
print("\n" + "="*60 + "\nStep 1: Running Main Graph\n" + "="*60)
main_graph = create_main_graph()
context = main_graph.run(context)

recommendations = context.get_cache("recommendation", [])
print(f"\n[추천 종목] {', '.join(recommendations)}")

# Trader Graph 실행 (각 종목별)
print("\n" + "="*60 + "\nStep 2: Running Trader Graph\n" + "="*60)
for ticker in recommendations:
    print(f"\nProcessing {ticker}...")
    context.set_cache(ticker=ticker)
    trader_graph = create_trader_graph()
    context = trader_graph.run(context)

print("\n" + "="*60 + "\n테스트 완료\n" + "="*60)
