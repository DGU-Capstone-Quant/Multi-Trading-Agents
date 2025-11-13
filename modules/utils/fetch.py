# modules/utils/fetch.py
from .stock_api import *
from .constant import AVAILABLE_TOPICS
from datetime import datetime as dt
import pandas as pd

def fetch_news_sentiment(ticker: str="", topics: list[str]=[], limit: int=50, date_to: str="", days: int=7, apikey: str="") -> dict:
    # topics 필터링 시 AVAILABLE_TOPICS을 기준으로 하여 순서 유지, 캐싱 중복 방지
    valid_topics = [topic for topic in AVAILABLE_TOPICS if topic in topics]

    topics_str = ','.join(valid_topics)
    time_from = ""
    time_to = ""
    if date_to:
        date_to_dt = dt.strptime(date_to, "%Y%m%d")
        time_to = date_to_dt.strftime("%Y%m%dT%H%M")
        time_from_dt = date_to_dt - pd.Timedelta(days=days)
        time_from = time_from_dt.strftime("%Y%m%dT%H%M")
    
    content = get_news_sentiment(ticker=ticker, topics=topics_str, limit=limit,
                                 time_from=time_from, time_to=time_to, apikey=apikey)
    
    content = content.get("feed", [])
    return content


def fetch_time_series_intraday(ticker: str, interval: str, date: str = "", apikey: str = "") -> pd.DataFrame:
    if not date:
        df = get_time_series_intraday(ticker=ticker, interval=interval, apikey=apikey)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    month = dt.strptime(date, "%Y%m%d").strftime("%Y-%m")
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
    print(fetch_news_sentiment(ticker="AAPL", topics=["technology", "earnings"], limit=10, date_to="20250613", days=3))
    
    print(fetch_time_series_intraday(ticker="AAPL", interval="5min"))
    print(fetch_time_series_intraday(ticker="AAPL", interval="5min", date="20250613"))
    
    # 아래 함수들은 date_from 미지정 시 전체 데이터 반환합니다.
    print(fetch_time_series_daily(ticker="AAPL", date_from="20230101", date_to="20230131"))
    print(fetch_time_series_weekly(ticker="AAPL", date_from="20220101", date_to="20221231"))
    print(fetch_time_series_monthly(ticker="AAPL", date_from="20200101", date_to="20221231"))