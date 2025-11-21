import requests
import json
from datetime import datetime

# 실전투자 주소: https://openapi.koreainvestment.com:9443
# 모의투자 주소: https://openapivts.koreainvestment.com:29443

class RealTrader:
    def __init__(self, app_key: str, app_secret: str, cano: str, acnt_prdt_cd: str = "01", is_mock: bool = False):
        """
        한국투자증권 API를 통한 실전/모의 거래 클래스

        Args:
            app_key: 앱 키
            app_secret: 앱 시크릿
            cano: 계좌번호 8자리 (예: 50108631)
            acnt_prdt_cd: 계좌상품코드 2자리 (기본값: "01")
            is_mock: True이면 모의투자, False이면 실전투자
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.cano = cano
        self.acnt_prdt_cd = acnt_prdt_cd
        self.is_mock = is_mock

        # URL 설정
        self.base_url = "https://openapivts.koreainvestment.com:29443" if is_mock else "https://openapi.koreainvestment.com:9443"

        # 계좌번호 형식 검증
        if len(self.cano) != 8:
            print(f"[경고] CANO는 8자리여야 합니다. 현재: {self.cano} ({len(self.cano)}자리)")

        if len(self.acnt_prdt_cd) != 2:
            print(f"[경고] ACNT_PRDT_CD는 2자리여야 합니다. 현재: {self.acnt_prdt_cd} ({len(self.acnt_prdt_cd)}자리)")

        # 토큰 발급
        self.access_token = self._get_access_token()
        print(f"[초기화 완료] {'모의투자' if is_mock else '실전투자'} 모드")
        print(f"[계좌번호] CANO: {self.cano}, 상품코드: {self.acnt_prdt_cd}")

    def _get_access_token(self):
        """OAuth 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }

        res = requests.post(url, headers=headers, data=json.dumps(body))

        if res.status_code != 200:
            raise Exception(f"토큰 발급 실패: {res.text}")

        token = res.json().get("access_token")
        print(f"[토큰 발급 완료]")
        return token

    def _get_hashkey(self, datas: dict):
        """해시키 발급"""
        url = f"{self.base_url}/uapi/hashkey"
        headers = {
            'content-Type': 'application/json',
            'appKey': self.app_key,
            'appSecret': self.app_secret,
        }
        res = requests.post(url, headers=headers, data=json.dumps(datas))
        return res.json()["HASH"]

    def get_current_price(self, stock_no: str):
        """국내 주식 현재가 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": "FHKST01010100"
        }

        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_no
        }

        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200 and res.json()["rt_cd"] == "0":
            output = res.json()['output']
            price = output['stck_prpr']
            print(f"\n[현재가 조회] {stock_no}")
            print(f"  - 현재가: {price}원")
            print(f"  - 전일대비: {output['prdy_ctrt']}%")
            return output
        else:
            print(f"[현재가 조회 실패] {res.json()}")
            return None

    def get_balance(self):
        """국내 주식 잔고 조회"""
        tr_id = "TTTC8434R" if not self.is_mock else "VTTC8434R"
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": tr_id
        }

        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "01",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200 and res.json()["rt_cd"] == "0":
            stocks = {}
            print("\n[보유 주식 조회]")
            for stock in res.json()['output1']:
                if int(stock["hldg_qty"]) > 0:
                    stocks[stock["pdno"]] = {
                        "name": stock["prdt_name"],
                        "qty": int(stock["hldg_qty"]),
                        "avg_price": float(stock["pchs_avg_pric"]),
                        "current_price": float(stock["prpr"]),
                        "profit_rate": float(stock["evlu_pfls_rt"])
                    }
                    print(f"  - {stock['prdt_name']} ({stock['pdno']}): {stock['hldg_qty']}주, 수익률 {stock['evlu_pfls_rt']}%")

            if not stocks:
                print("  - 보유 주식 없음")

            return stocks
        else:
            print(f"[잔고 조회 실패] {res.json()}")
            return None

    def get_cash(self):
        """매수 가능 현금 조회"""
        tr_id = "TTTC8908R" if not self.is_mock else "VTTC8908R"
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-psbl-order"

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": tr_id
        }

        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "PDNO": "005930",
            "ORD_UNPR": "0",
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "N",
            "OVRS_ICLD_YN": "N"
        }

        print(f"[계좌번호 확인] CANO: {self.cano}, ACNT_PRDT_CD: {self.acnt_prdt_cd}")

        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200 and res.json()["rt_cd"] == "0":
            output = res.json()['output']
            cash = int(output['ord_psbl_cash'])
            print(f"\n[매수 가능 현금] {cash:,}원")
            return output
        else:
            print(f"[현금 조회 실패] {res.json()}")
            return None

    def order(self, stock_no: str, qty: int, order_type: str, price: int = 0):
        """
        주식 주문

        Args:
            stock_no: 종목코드 (예: 005930)
            qty: 주문 수량
            order_type: "BUY" 또는 "SELL"
            price: 지정가 (0이면 시장가)
        """
        if order_type not in ["BUY", "SELL"]:
            print(f"[주문 실패] 잘못된 주문 타입: {order_type}")
            return None

        # TR_ID 설정
        if order_type == "BUY":
            tr_id = "TTTC0802U" if not self.is_mock else "VTTC0802U"
        else:
            tr_id = "TTTC0801U" if not self.is_mock else "VTTC0801U"

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"

        # 주문 데이터
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "PDNO": stock_no,
            "ORD_DVSN": "01" if price == 0 else "00",  # 01: 시장가, 00: 지정가
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price) if price > 0 else "0"
        }

        # 헤더 설정
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": tr_id,
            "hashkey": self._get_hashkey(body)
        }

        # 주문 실행
        res = requests.post(url, headers=headers, data=json.dumps(body))

        result = {
            "timestamp": datetime.now().isoformat(),
            "stock_no": stock_no,
            "order_type": order_type,
            "qty": qty,
            "price": price,
            "status_code": res.status_code,
            "response": res.json() if res.status_code == 200 else res.text
        }

        if res.status_code == 200 and int(res.json()["rt_cd"]) < 2:
            print(f"\n[주문 성공]")
            print(f"  - 종목: {stock_no}")
            print(f"  - 타입: {order_type}")
            print(f"  - 수량: {qty}주")
            print(f"  - 가격: {'시장가' if price == 0 else f'{price}원'}")

            # output 키 존재 여부 확인
            response_data = res.json()
            if 'output' in response_data and 'ODNO' in response_data['output']:
                print(f"  - 주문번호: {response_data['output']['ODNO']}")
            else:
                print(f"  - 전체 응답: {response_data}")
        else:
            print(f"\n[주문 실패]")
            print(f"  - 응답: {res.json()}")

        # 로그 저장
        log_file = f"logs/orders/{stock_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import os
        os.makedirs("logs/orders", exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    # ===== 해외주식 거래 메서드 =====

    def get_overseas_current_price(self, stock_no: str, exchange: str = "NASD"):
        """
        해외 주식 현재가 조회

        Args:
            stock_no: 종목코드 (예: AAPL, GOOGL)
            exchange: 거래소 코드 (NASD=나스닥, NYSE=뉴욕, AMEX=아멕스, 기본값: NASD)
        """
        # 해외주식 현재가 시세 조회
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": "HHDFS00000300"  # 해외주식 현재가 시세 (실전/모의 공통)
        }

        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": stock_no
        }

        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200 and res.json()["rt_cd"] == "0":
            output = res.json()['output']

            # 실제 응답 필드 확인
            price = output.get('last', '').strip() or output.get('curr', '').strip() or 'N/A'
            change_rate = output.get('rate', '').strip() or 'N/A'
            high = output.get('high', '').strip() or 'N/A'
            low = output.get('low', '').strip() or 'N/A'

            print(f"\n[해외주식 현재가 조회] {stock_no} ({exchange})")
            print(f"  - 현재가: ${price}")
            print(f"  - 전일대비: {change_rate}%")
            print(f"  - 고가: ${high}")
            print(f"  - 저가: ${low}")

            # 만약 모든 값이 비어있다면 경고 메시지 출력
            if price == 'N/A' and change_rate == 'N/A':
                print(f"\n[경고] 시세 데이터가 비어있습니다.")
                print(f"[경고] 거래 시간 외이거나 실시간 시세 권한이 없을 수 있습니다.")
                print(f"[참고] 미국 증시 거래 시간: 한국시간 23:30~06:00 (서머타임 22:30~05:00)")

            return output
        else:
            print(f"[해외주식 현재가 조회 실패] {res.json()}")
            return None

    def get_overseas_daily_price(self, stock_no: str, exchange: str = "NASD"):
        """
        해외 주식 일별 시세 조회 (장 마감 후에도 전일 종가 조회 가능)

        Args:
            stock_no: 종목코드 (예: AAPL, GOOGL)
            exchange: 거래소 코드 (NASD=나스닥, NYSE=뉴욕, AMEX=아멕스, 기본값: NASD)
        """
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/dailyprice"

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": "HHDFS76240000"  # 해외주식 기간별시세
        }

        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": stock_no,
            "GUBN": "0",  # 0: 일봉, 1: 주봉, 2: 월봉
            "BYMD": "",   # 조회 기준일자 (공백: 최근일자)
            "MODP": "1"   # 0: 수정주가 미반영, 1: 수정주가 반영
        }

        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200 and res.json()["rt_cd"] == "0":
            output2 = res.json().get('output2', [])
            if output2 and len(output2) > 0:
                latest = output2[0]  # 가장 최근 데이터
                print(f"\n[해외주식 일별 시세] {stock_no} ({exchange})")
                print(f"  - 날짜: {latest.get('xymd', 'N/A')}")
                print(f"  - 종가: ${latest.get('clos', 'N/A')}")
                print(f"  - 시가: ${latest.get('open', 'N/A')}")
                print(f"  - 고가: ${latest.get('high', 'N/A')}")
                print(f"  - 저가: ${latest.get('low', 'N/A')}")
                print(f"  - 거래량: {latest.get('tvol', 'N/A')}")
                return latest
            else:
                print(f"[해외주식 일별 시세 조회 실패] 데이터가 없습니다.")
                return None
        else:
            print(f"[해외주식 일별 시세 조회 실패] {res.json()}")
            return None

    def get_overseas_balance(self):
        """해외 주식 잔고 조회"""
        tr_id = "TTTS3012R" if not self.is_mock else "VTTS3012R"
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": tr_id
        }

        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": "NASD",  # 나스닥 기준
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }

        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200 and res.json()["rt_cd"] == "0":
            stocks = {}
            print("\n[해외 보유 주식 조회]")
            for stock in res.json().get('output1', []):
                if int(stock.get("ovrs_cblc_qty", 0)) > 0:
                    stocks[stock["ovrs_pdno"]] = {
                        "name": stock.get("ovrs_item_name", ""),
                        "qty": int(stock["ovrs_cblc_qty"]),
                        "avg_price": float(stock.get("pchs_avg_pric", 0)),
                        "current_price": float(stock.get("now_pric2", 0)),
                        "profit_rate": float(stock.get("evlu_pfls_rt", 0))
                    }
                    print(f"  - {stock.get('ovrs_item_name', '')} ({stock['ovrs_pdno']}): {stock['ovrs_cblc_qty']}주, 수익률 {stock.get('evlu_pfls_rt', 0)}%")

            if not stocks:
                print("  - 해외 보유 주식 없음")

            return stocks
        else:
            print(f"[해외 잔고 조회 실패] {res.json()}")
            return None

    def get_overseas_cash(self, currency: str = "USD"):
        """
        해외주식 매수 가능 현금 조회

        Args:
            currency: 통화 코드 (USD, JPY, CNY 등)
        """
        tr_id = "TTTS3007R" if not self.is_mock else "VTTS3007R"
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-psamount"

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": tr_id
        }

        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": "NASD",
            "OVRS_ORD_UNPR": "0",
            "ITEM_CD": "AAPL"
        }

        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200 and res.json()["rt_cd"] == "0":
            output = res.json()['output']
            cash = float(output.get('ovrs_ord_psbl_amt', 0))
            print(f"\n[해외주식 매수 가능 현금] ${cash:,.2f}")
            return output
        else:
            print(f"[해외 현금 조회 실패] {res.json()}")
            return None

    def order_overseas(self, stock_no: str, qty: int, order_type: str, exchange: str = "NASD", price: float = 0):
        """
        해외 주식 주문

        Args:
            stock_no: 종목코드 (예: AAPL, GOOGL)
            qty: 주문 수량
            order_type: "BUY" 또는 "SELL"
            exchange: 거래소 코드 (NASD=나스닥, NYSE=뉴욕, AMEX=아멕스)
            price: 지정가 (0이면 시장가, USD 기준)
        """
        if order_type not in ["BUY", "SELL"]:
            print(f"[주문 실패] 잘못된 주문 타입: {order_type}")
            return None

        # TR_ID 설정
        if order_type == "BUY":
            tr_id = "TTTS0308U" if not self.is_mock else "VTTS0308U"
        else:
            tr_id = "TTTS0307U" if not self.is_mock else "VTTS0307U"

        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"

        # 주문 데이터
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": exchange,
            "PDNO": stock_no,
            "ORD_DVSN": "00" if price > 0 else "01",  # 00: 지정가, 01: 시장가
            "ORD_QTY": str(qty),
            "OVRS_ORD_UNPR": str(price) if price > 0 else "0",
            "ORD_SVR_DVSN_CD": "0"
        }

        # 헤더 설정
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": tr_id,
            "hashkey": self._get_hashkey(body)
        }

        # 주문 실행
        res = requests.post(url, headers=headers, data=json.dumps(body))

        result = {
            "timestamp": datetime.now().isoformat(),
            "stock_no": stock_no,
            "exchange": exchange,
            "order_type": order_type,
            "qty": qty,
            "price": price,
            "status_code": res.status_code,
            "response": res.json() if res.status_code == 200 else res.text
        }

        if res.status_code == 200 and int(res.json()["rt_cd"]) < 2:
            print(f"\n[해외주식 주문 성공]")
            print(f"  - 종목: {stock_no} ({exchange})")
            print(f"  - 타입: {order_type}")
            print(f"  - 수량: {qty}주")
            print(f"  - 가격: {'시장가' if price == 0 else f'${price}'}")

            response_data = res.json()
            if 'output' in response_data and 'ODNO' in response_data['output']:
                print(f"  - 주문번호: {response_data['output']['ODNO']}")
            else:
                print(f"  - 전체 응답: {response_data}")
        else:
            print(f"\n[해외주식 주문 실패]")
            print(f"  - 응답: {res.json()}")

        # 로그 저장
        log_file = f"logs/orders/overseas_{stock_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import os
        os.makedirs("logs/orders", exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result


def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("한국투자증권 실전/모의 거래 테스트")
    print("=" * 60)

    # API 키 설정 (미리 입력된 값)
    app_key = "PS4zRGLHMEMJnPlKbfMAc5sHRE3Ou082JC67"
    app_secret = "PC8ZHFBwvWaKdXqfRhSPGBWtuPuqqSU9pxWzqRVexSWD4EJc4iZ9R3fRDJ4zQZjb4geIaOBzjygQg4evhfdmWY8aac2wSwwBOkb5KWlx3LmeXtpsrDUohFtUwL4hHPiGHPZ4i72UblMDYRz5WtnsbTC31teQkPzNrqqBkAHnOZZ3xrojgQ4="

    print("\n[API 키 자동 설정 완료]")

    # 실전/모의 선택
    is_mock_input = input("모의투자? (y/n, 기본값 y): ").strip().lower()
    is_mock = True if is_mock_input in ["", "y", "yes"] else False

    # 계좌번호 입력
    cano = input("계좌번호 8자리 (예: 50108631): ").strip()
    acnt_prdt_cd = input("계좌상품코드 2자리 (기본값 01): ").strip()
    if not acnt_prdt_cd:
        acnt_prdt_cd = "01"

    if not is_mock:
        confirm = input("⚠️  실전투자 모드입니다. 계속하시겠습니까? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("테스트를 취소합니다.")
            return

    # Trader 초기화
    try:
        trader = RealTrader(
            app_key=app_key,
            app_secret=app_secret,
            cano=cano,
            acnt_prdt_cd=acnt_prdt_cd,
            is_mock=is_mock
        )
    except Exception as e:
        print(f"\n[초기화 실패] {e}")
        return

    # 테스트 메뉴
    while True:
        print("\n" + "=" * 60)
        print("[테스트 메뉴]")
        print("=== 국내주식 ===")
        print("1. 현재가 조회")
        print("2. 보유 주식 조회")
        print("3. 매수 가능 현금 조회")
        print("4. 주식 매수")
        print("5. 주식 매도")
        print("\n=== 해외주식 ===")
        print("6. 해외 현재가 조회")
        print("7. 해외 보유 주식 조회")
        print("8. 해외 매수 가능 현금 조회")
        print("9. 해외 주식 매수")
        print("10. 해외 주식 매도")
        print("\n0. 종료")
        print("=" * 60)

        choice = input("\n선택: ").strip()

        if choice == "0":
            print("테스트를 종료합니다.")
            break

        # 국내주식
        elif choice == "1":
            stock_no = input("종목코드 (예: 005930): ").strip()
            trader.get_current_price(stock_no)

        elif choice == "2":
            trader.get_balance()

        elif choice == "3":
            trader.get_cash()

        elif choice == "4":
            stock_no = input("종목코드 (예: 005930): ").strip()
            qty = int(input("수량: ").strip())
            price_input = input("가격 (0이면 시장가): ").strip()
            price = int(price_input) if price_input else 0

            confirm = input(f"\n{stock_no} {qty}주를 {'시장가' if price == 0 else f'{price}원'}에 매수하시겠습니까? (y/n): ").strip().lower()
            if confirm == "y":
                trader.order(stock_no, qty, "BUY", price)

        elif choice == "5":
            stock_no = input("종목코드 (예: 005930): ").strip()
            qty = int(input("수량: ").strip())
            price_input = input("가격 (0이면 시장가): ").strip()
            price = int(price_input) if price_input else 0

            confirm = input(f"\n{stock_no} {qty}주를 {'시장가' if price == 0 else f'{price}원'}에 매도하시겠습니까? (y/n): ").strip().lower()
            if confirm == "y":
                trader.order(stock_no, qty, "SELL", price)

        # 해외주식
        elif choice == "6":
            stock_no = input("종목코드 (예: AAPL, GOOGL): ").strip()
            exchange = input("거래소 (NASD/NYSE/AMEX, 기본값 NASD): ").strip().upper()
            if not exchange:
                exchange = "NASD"
            trader.get_overseas_current_price(stock_no, exchange)

        elif choice == "7":
            trader.get_overseas_balance()

        elif choice == "8":
            trader.get_overseas_cash()

        elif choice == "9":
            stock_no = input("종목코드 (예: AAPL, GOOGL): ").strip()
            exchange = input("거래소 (NASD/NYSE/AMEX, 기본값 NASD): ").strip().upper()
            if not exchange:
                exchange = "NASD"
            qty = int(input("수량: ").strip())
            price_input = input("가격 (0이면 시장가, USD 기준): ").strip()
            price = float(price_input) if price_input else 0

            confirm = input(f"\n{stock_no} {qty}주를 {'시장가' if price == 0 else f'${price}'}에 매수하시겠습니까? (y/n): ").strip().lower()
            if confirm == "y":
                trader.order_overseas(stock_no, qty, "BUY", exchange, price)

        elif choice == "10":
            stock_no = input("종목코드 (예: AAPL, GOOGL): ").strip()
            exchange = input("거래소 (NASD/NYSE/AMEX, 기본값 NASD): ").strip().upper()
            if not exchange:
                exchange = "NASD"
            qty = int(input("수량: ").strip())
            price_input = input("가격 (0이면 시장가, USD 기준): ").strip()
            price = float(price_input) if price_input else 0

            confirm = input(f"\n{stock_no} {qty}주를 {'시장가' if price == 0 else f'${price}'}에 매도하시겠습니까? (y/n): ").strip().lower()
            if confirm == "y":
                trader.order_overseas(stock_no, qty, "SELL", exchange, price)

        else:
            print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()
