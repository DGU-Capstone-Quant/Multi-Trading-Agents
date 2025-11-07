# modules/utils/stock_api.py
import yfinance as yf
from defeatbeta_api.data.ticker import Ticker as dfTicker

def fetch_stock_data_dfa(ticker, start_date, end_date, interval="1m"):
    data = dfTicker(ticker).price()

def fetch_stock_data_yf(ticker, period="1d", interval="1m", end=None):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period, interval=interval, end=end)
    return data


def fetch_stock_data(ticker, period="1d", interval="1m", end=None):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period, interval=interval, end=end)
    return data


if __name__ == "__main__":
    ticker = "005930.KS"
    data = fetch_stock_data(ticker)
    print(data)