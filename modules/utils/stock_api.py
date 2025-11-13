# modules/utils/stock_api.py
import os
import requests
import pandas as pd
from io import StringIO
from datetime import datetime as dt


URL = "https://alpha-vantage.p.rapidapi.com/query"

def _get_file_path_by_query(**params) -> str:
    file_path = f"./cache/stock_api/{params.get('function', 'UNKNOWN')}/"
    date = params.get("month", "")
    if not date:
        date = dt.now().strftime("%Y%m%d%H%M") # 실시간 데이터 캐싱용
    else:
        date = dt.strptime(date, "%Y-%m").strftime("%Y%m")

    if file_path.endswith("NEWS_SENTIMENT/"):
        file_path += f"{params.get('tickers','') }_" +\
                     f"{params.get('topics','')}_" +\
                     f"{params.get('limit','')}_" +\
                     f"{params.get('time_from','')}_" +\
                     f"{params.get('time_to', dt.now().strftime('%Y%m%d%H'))}.json"
    elif file_path.endswith("TIME_SERIES_INTRADAY/"):
        file_path += f"{params.get('symbol','')}_" +\
                     f"{params.get('interval','')}_" +\
                     f"{params.get('outputsize','')}_" +\
                     f"{date}.csv"
    elif file_path.endswith("TIME_SERIES_DAILY_ADJUSTED/"):
        file_path += f"{params.get('symbol','')}_" +\
                     f"{dt.now().strftime('%Y%m%d')}.csv"
    elif file_path.endswith("TIME_SERIES_WEEKLY_ADJUSTED/"):
        file_path += f"{params.get('symbol','')}_" +\
                     f"{dt.now().strftime('%Y%m%d')}.csv"
    elif file_path.endswith("TIME_SERIES_MONTHLY_ADJUSTED/"):
        file_path += f"{params.get('symbol','')}_" +\
                     f"{dt.now().strftime('%Y%m')}.csv"

    return file_path

def _get_response_by_query(**params) -> dict:
    apikey = params.pop("apikey", "")
    if not apikey:
        apikey = os.getenv("RAPID_API_KEY", "")
    if not apikey:
        raise ValueError("API key is required: 환경변수 RAPID_API_KEY에 alpha-vantage용 RapidAPI 키를 설정해야 함")
    filtered_params = {k: v for k, v in params.items() if v != ""}
    res = requests.get(url=URL, params=filtered_params,
                       headers={
                            "x-rapidapi-host": "alpha-vantage.p.rapidapi.com",
                            "x-rapidapi-key": apikey
                        })
    
    file_path = _get_file_path_by_query(**params)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb') as f:
        f.write(res.content)

    content = {}
    if filtered_params.get("datatype", "json") == "csv":
        content['csv'] = pd.read_csv(StringIO(res.text))
    else:
        content = res.json()

    return content

def _get_file_by_query(**params) -> dict:
    file_path = _get_file_path_by_query(**params)
    if not os.path.exists(file_path):
        return None

    content = {}
    if file_path.endswith('.csv'):
        content['csv'] = pd.read_csv(file_path)
    elif file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            content = f.read()
        content = pd.read_json(StringIO(content))
    else:
        return None

    return content
    

def _get_query_data(**params) -> dict:
    cache = _get_file_by_query(**params)
    if cache is not None:
        return cache
    content = _get_response_by_query(**params)
    return content


def get_news_sentiment(ticker: str="", topics: str="", limit: int=50, time_from: str="", time_to: str="", apikey: str="") -> dict:
    content = _get_query_data(
        function="NEWS_SENTIMENT",
        tickers=ticker,
        topics=topics,
        limit=limit,
        time_from=time_from,
        time_to=time_to,
        apikey=apikey,
    )
    return content

def get_time_series_intraday(ticker: str="", interval: str="5min", month: str = "", apikey: str="") -> pd.DataFrame:
    outputsize = "full" if len(month) == 7 else "compact"
    content = _get_query_data(
        function="TIME_SERIES_INTRADAY",
        symbol=ticker,
        interval=interval, # 5min, 15min, 30min, 60min
        adjusted="true",
        month=month, # month format: YYYY-MM
        outputsize=outputsize,
        apikey=apikey,
        datatype="csv",
    )
    return content.get('csv', pd.DataFrame())

def get_time_series_daily(ticker: str="", apikey: str="") -> pd.DataFrame:
    content = _get_query_data(
        function="TIME_SERIES_DAILY_ADJUSTED",
        symbol=ticker,
        outputsize="full",
        apikey=apikey,
        datatype="csv",
    )
    return content.get('csv', pd.DataFrame())

def get_time_series_weekly(ticker: str="", apikey: str="") -> pd.DataFrame:
    content = _get_query_data(
        function="TIME_SERIES_WEEKLY_ADJUSTED",
        symbol=ticker,
        apikey=apikey,
        datatype="csv",
    )
    return content.get('csv', pd.DataFrame())

def get_time_series_monthly(ticker: str="", apikey: str="") -> pd.DataFrame:
    content = _get_query_data(
        function="TIME_SERIES_MONTHLY_ADJUSTED",
        symbol=ticker,
        apikey=apikey,
        datatype="csv",
    )
    return content.get('csv', pd.DataFrame())


if __name__ == "__main__":
    # Example usage
    apikey = os.getenv("RAPID_API_KEY", "")
    get_news_sentiment(ticker="AAPL", limit=10, apikey=apikey)
    get_time_series_intraday(ticker="AAPL", interval="15min", month="2025-07", apikey=apikey)
    get_time_series_daily(ticker="AAPL", apikey=apikey)
