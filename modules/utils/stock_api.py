# modules/utils/stock_api.py
import yfinance as yf

def fetch_stock_data(ticker, period="1d", interval="1h"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period, interval=interval)
    return data
