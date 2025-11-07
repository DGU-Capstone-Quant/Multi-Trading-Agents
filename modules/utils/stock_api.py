# modules/utils/stock_api.py
import yfinance as yf

def fetch_stock_data_yf(ticker, period="1d", interval="1m", end=None):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period, interval=interval, end=end)
    return data


def fetch_stock_data(ticker, period="1d", interval="1m", end=None):
    data = fetch_stock_data_yf(ticker, period=period, interval=interval, end=end)
    return data


if __name__ == "__main__":
    ticker = "AAPL"
    data = fetch_stock_data(ticker)
    print(data)

import requests

# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey=demo'
r = requests.get(url)
data = r.json()

print(data)