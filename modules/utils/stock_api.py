# modules/utils/stock_api.py
import yfinance as yf

def fetch_stock_data(ticker, period="1d", interval="1m", end=None):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period, interval=interval, end=end)
    return data


if __name__ == "__main__":
    ticker = "005930.KS"
    data = fetch_stock_data(ticker)
    print(data)