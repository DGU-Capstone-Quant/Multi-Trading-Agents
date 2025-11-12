# modules/utils/fetch.py
from .stock_api import *
from datetime import datetime
import pandas as pd


def fetch_news_sentiment(ticker: str, date: str, apikey: str = "") -> dict:
    pass # 구현할 예정

def fetch_time_series_intraday(ticker: str, interval: str, date: str = "", apikey: str = "") -> pd.DataFrame:
    if not date:
        df = get_time_series_intraday(ticker=ticker, interval=interval, apikey=apikey)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    month = datetime.strptime(date, "%Y%m%d").strftime("%Y-%m")
    df = get_time_series_intraday(ticker=ticker, interval=interval, month=month, apikey=apikey)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    filtered_df = df[df['timestamp'].dt.strftime("%Y%m%d") == date]
    return filtered_df

def fetch_time_series_daily(ticker: str, date_from: str = "", date_to: str = "", apikey: str = "") -> pd.DataFrame:
    df = get_time_series_daily(ticker=ticker, apikey=apikey)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    if date_from:
        df = df[df['timestamp'] >= pd.to_datetime(date_from)]
    if date_to:
        df = df[df['timestamp'] <= pd.to_datetime(date_to)]
    return df

def fetch_time_series_weekly(ticker: str, date_from: str = "", date_to: str = "", apikey: str = "") -> pd.DataFrame:
    df = get_time_series_weekly(ticker=ticker, apikey=apikey)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    if date_from:
        df = df[df['timestamp'] >= pd.to_datetime(date_from)]
    if date_to:
        df = df[df['timestamp'] <= pd.to_datetime(date_to)]
    return df

def fetch_time_series_monthly(ticker: str, date_from: str = "", date_to: str = "", apikey: str = "") -> pd.DataFrame:
    df = get_time_series_monthly(ticker=ticker, apikey=apikey)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    if date_from:
        df = df[df['timestamp'] >= pd.to_datetime(date_from)]
    if date_to:
        df = df[df['timestamp'] <= pd.to_datetime(date_to)]
    return df


# test: python -m modules.utils.fetch
if __name__ == "__main__":
    # module.utils.fetch_time_series_intraday 이렇게 사용하면 됩니다.
    print(fetch_time_series_intraday(ticker="AAPL", interval="5min"))
    print(fetch_time_series_intraday(ticker="AAPL", interval="5min", date="20250613"))
    
    # 아래 함수들은 date_from 미지정 시 전체 데이터 반환합니다.
    print(fetch_time_series_daily(ticker="AAPL", date_from="20230101", date_to="20230131"))
    print(fetch_time_series_weekly(ticker="AAPL", date_from="20220101", date_to="20221231"))
    print(fetch_time_series_monthly(ticker="AAPL", date_from="20200101", date_to="20221231"))