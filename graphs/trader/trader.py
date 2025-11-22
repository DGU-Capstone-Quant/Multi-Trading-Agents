import requests
import json
from datetime import datetime
from pathlib import Path


class KISTrader:
    def __init__(self, app_key: str, app_secret: str, account_no: str, is_mock: bool = True):
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no
        self.is_mock = is_mock

        self.base_url = "https://openapivts.koreainvestment.com:29443" if is_mock else "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        self._get_access_token()

    def _get_access_token(self):
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }

        res = requests.post(url, headers=headers, data=json.dumps(body))
        if res.status_code != 200:
            raise Exception(f"Failed to get access token: {res.text}")

        self.access_token = res.json().get("access_token")
        print(f"[KIS] Access token obtained")

    def _get_headers(self, tr_id: str):
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id
        }

    def execute_order(self, ticker: str, decision: str, quantity: int, price: int = 0):
        if decision not in ["BUY", "SELL"]:
            print(f"[KIS] Invalid decision: {decision}. Order not executed.")
            return None

        cano, acnt_prdt_cd = self.account_no.split("-")

        if decision == "BUY":
            tr_id = "VTTC0802U" if self.is_mock else "TTTC0802U"
        else:
            tr_id = "VTTC0801U" if self.is_mock else "TTTC0801U"

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"

        body = {
            "CANO": cano,
            "ACNT_PRDT_CD": acnt_prdt_cd,
            "PDNO": ticker,
            "ORD_DVSN": "01",
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if price > 0 else "0"
        }

        res = requests.post(url, headers=self._get_headers(tr_id), data=json.dumps(body))

        result = {
            "status_code": res.status_code,
            "response": res.json() if res.status_code == 200 else res.text,
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "ticker": ticker,
            "quantity": quantity,
            "price": price
        }

        if res.status_code == 200:
            print(f"\n[KIS] Order executed successfully:")
            print(f"  - {decision} {quantity} shares of {ticker}")
            if price > 0:
                print(f"  - Price: {price} KRW")
        else:
            print(f"\n[KIS] Order failed: {result['response']}")

        log_dir = Path("logs/kis_orders")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        return result


if __name__ == "__main__":
    trader = KISTrader(
        app_key="YOUR_APP_KEY",
        app_secret="YOUR_APP_SECRET",
        account_no="12345678-01",
        is_mock=True
    )

    result = trader.execute_order(
        ticker="005930",
        decision="BUY",
        quantity=1,
        price=70000
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
