# modules/utils/fetch.py
from .stock_api import fetch_stock_data

def fetch_data_days(ticker: str, days: int, end=None):
    period = f"{days}d"
    data = fetch_stock_data(ticker, period=period, interval="1d", end=end)
    return data

def fetch_data_hours(ticker: str, end=None):
    data = fetch_stock_data(ticker, period="1d", interval="1h", end=end)
    return data

def fetch_data_minutes(ticker: str, end=None):
    data = fetch_stock_data(ticker, period="1d", interval="1m", end=end)
    return data