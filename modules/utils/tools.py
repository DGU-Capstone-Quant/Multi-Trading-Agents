# modules/utils/tools.py
from .fetch import *

# definition
FINANCIAL_TOOLS = []
NEWS_TOOLS = []

def _get_func_dict(func, desc: str, params: dict, context_params: dict) -> dict:
    return {
        'func': func,
        'name': func.__name__,
        'desc': desc,
        'params': params,
        'context_params': context_params,
    }


### Financial Analysis Tools
def get_latest_qoute(ticker: str, date: str="", apikey: str="") -> dict:
    df = fetch_time_series_intraday(ticker=ticker, interval="5min", date=date, apikey=apikey)
    df = df.sort_values(by='timestamp', ascending=False).reset_index(drop=True)
    return {
        'open': df['open'].iloc[-1],
        'high': max(df['high']),
        'low': min(df['low']),
        'latest_price': df['close'].iloc[0],
        'volume': sum(df['volume']),
    }
def get_latest_qoute_func():
    desc = "Fetch the latest stock quote for a given ticker symbol."
    params = {}
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(get_latest_qoute, desc, params, context_params)


def get_price_summary_for_date(ticker: str, date: str="", apikey: str="") -> dict:
    df = fetch_time_series_daily(ticker=ticker, days=7, date_to=date, apikey=apikey)
    return {
        'open': df['open'].iloc[0],
        'high': df['high'].iloc[0],
        'low': df['low'].iloc[0],
        'close': df['close'].iloc[0],
        'volume': df['volume'].iloc[0],
    }
def get_price_summary_for_date_func():
    desc = "Fetch the stock quote for the previous trading day for a given ticker symbol."
    params = {}
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(get_price_summary_for_date, desc, params, context_params)


def get_price_summary_for_week(ticker: str, date: str="", apikey: str="") -> dict:
    df = fetch_time_series_weekly(ticker=ticker, weeks=4, date_to=date, apikey=apikey)
    return {
        'open': df['open'].iloc[0],
        'high': df['high'].iloc[0],
        'low': df['low'].iloc[0],
        'close': df['close'].iloc[0],
        'volume': df['volume'].iloc[0],
    }
def get_price_summary_for_week_func():
    desc = "Fetch the stock quote summary for the last week for a given ticker symbol."
    params = {}
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(get_price_summary_for_week, desc, params, context_params)


def get_price_summary_for_month(ticker: str, date: str="", apikey: str="") -> dict:
    df = fetch_time_series_monthly(ticker=ticker, months=12, date_to=date, apikey=apikey)
    return {
        'open': df['open'].iloc[0],
        'high': df['high'].iloc[0],
        'low': df['low'].iloc[0],
        'close': df['close'].iloc[0],
        'volume': df['volume'].iloc[0],
    }
def get_price_summary_for_month_func():
    desc = "Fetch the stock quote summary for the last month for a given ticker symbol."
    params = {}
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(get_price_summary_for_month, desc, params, context_params)


def get_historical_highs_lows(ticker: str, weeks: int, date: str="", apikey: str="") -> dict:
    df = fetch_time_series_weekly(ticker=ticker, weeks=weeks, date_to=date, apikey=apikey)
    return {
        'historical_high': max(df['high']),
        'historical_low': min(df['low']),
    }
def get_historical_highs_lows_func():
    desc = "Fetch the historical high and low prices over a specified number of weeks for a given ticker symbol."
    params = {
        'weeks': "number of weeks to look back, type: int"
    }
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(get_historical_highs_lows, desc, params, context_params)


def calculate_moving_average(ticker: str, days: int, date: str="", apikey: str="") -> float:
    df_daily = fetch_time_series_daily(ticker=ticker, days=days, date_to=date, apikey=apikey)
    latest_price = get_latest_qoute(ticker=ticker, date=date, apikey=apikey)['latest_price']
    # df is descending order by timestamp
    return {
        'moving_average': df_daily['close'].head(days).mean(),
        'price_on_date': latest_price,
        'position': "above" if latest_price > df_daily['close'].head(days).mean() else "below"
    }
def calculate_moving_average_func():
    desc = "Calculate the moving average over a specified number of days for a given ticker symbol and compare it to the latest price."
    params = {
        'days': "number of days for moving average calculation, type: int"
    }
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(calculate_moving_average, desc, params, context_params)


def calculate_macd(ticker: str, short_window: int=12, long_window: int=26, signal_window: int=9, date: str="", apikey: str="") -> dict:
    df_daily = fetch_time_series_daily(ticker=ticker, days=long_window + signal_window, date_to=date, apikey=apikey)
    df_daily = df_daily.sort_values(by='timestamp')  # ascending order for calculation

    df_daily['ema_short'] = df_daily['close'].ewm(span=short_window, adjust=False).mean()
    df_daily['ema_long'] = df_daily['close'].ewm(span=long_window, adjust=False).mean()
    df_daily['macd'] = df_daily['ema_short'] - df_daily['ema_long']
    df_daily['signal_line'] = df_daily['macd'].ewm(span=signal_window, adjust=False).mean()
    df_daily['oscillator'] = df_daily['macd'] - df_daily['signal_line']

    latest = df_daily.iloc[-1]
    return {
        'macd': latest['macd'],
        'signal_line': latest['signal_line'],
        'oscillator': latest['oscillator'],
    }
def calculate_macd_func():
    desc = "Calculate the MACD, signal line, and oscillator for a given ticker symbol."
    params = {
        'short_window': "short-term EMA window size, type: int, default: 12",
        'long_window': "long-term EMA window size, type: int, default: 26",
        'signal_window': "signal line EMA window size, type: int, default: 9",
    }
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(calculate_macd, desc, params, context_params)


def calculate_adx(ticker: str, period: int=14, date: str="", apikey: str="") -> float:
    df_daily = fetch_time_series_daily(ticker=ticker, days=period*3, date_to=date, apikey=apikey)
    df_daily = df_daily.sort_values(by='timestamp')  # ascending order for calculation

    df_daily['tr'] = pd.concat([
        df_daily['high'] - df_daily['low'],
        abs(df_daily['high'] - df_daily['close'].shift(1)),
        abs(df_daily['low'] - df_daily['close'].shift(1))
    ], axis=1).max(axis=1)

    df_daily['plus_dm'] = df_daily['high'].diff()
    df_daily['minus_dm'] = df_daily['low'].diff().abs()
    df_daily.loc[df_daily['plus_dm'] < 0, 'plus_dm'] = 0
    df_daily.loc[df_daily['minus_dm'] < 0, 'minus_dm'] = 0

    df_daily['atr'] = df_daily['tr'].rolling(window=period).mean()
    df_daily['plus_di'] = 100 * (df_daily['plus_dm'].rolling(window=period).mean() / df_daily['atr'])
    df_daily['minus_di'] = 100 * (df_daily['minus_dm'].rolling(window=period).mean() / df_daily['atr'])
    df_daily['dx'] = (abs(df_daily['plus_di'] - df_daily['minus_di']) / (df_daily['plus_di'] + df_daily['minus_di'])) * 100
    df_daily['adx'] = df_daily['dx'].rolling(window=period).mean()

    latest = df_daily.iloc[-1]
    return {
        'adx': latest['adx'],
        'plus_di': latest['plus_di'],
        'minus_di': latest['minus_di'],
    }
def calculate_adx_func():
    desc = "Calculate the Average Directional Index (ADX) for a given ticker symbol."
    params = {
        'period': "period for ADX calculation, type: int, default: 14",
    }
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(calculate_adx, desc, params, context_params)


def calculate_rsi(ticker: str, period: int=14, date: str="", apikey: str="") -> float:
    df_daily = fetch_time_series_daily(ticker=ticker, days=period*3, date_to=date, apikey=apikey)
    df_daily = df_daily.sort_values(by='timestamp')  # ascending order for calculation

    delta = df_daily['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    df_daily['rsi'] = 100 - (100 / (1 + rs))

    latest = df_daily.iloc[-1]
    return {
        'rsi': latest['rsi'],
    }
def calculate_rsi_func():
    desc = "Calculate the Relative Strength Index (RSI) for a given ticker symbol."
    params = {
        'period': "period for RSI calculation, type: int, default: 14",
    }
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(calculate_rsi, desc, params, context_params)


def calculate_stochastic_oscillator(ticker: str, k_period: int=14, d_period: int=3, date: str="", apikey: str="") -> dict:
    df_daily = fetch_time_series_daily(ticker=ticker, days=k_period*3, date_to=date, apikey=apikey)
    df_daily = df_daily.sort_values(by='timestamp')  # ascending order for calculation

    df_daily['lowest_low'] = df_daily['low'].rolling(window=k_period).min()
    df_daily['highest_high'] = df_daily['high'].rolling(window=k_period).max()
    df_daily['%K'] = 100 * ((df_daily['close'] - df_daily['lowest_low']) / (df_daily['highest_high'] - df_daily['lowest_low']))
    df_daily['%D'] = df_daily['%K'].rolling(window=d_period).mean()

    latest = df_daily.iloc[-1]
    return {
        '%K': latest['%K'],
        '%D': latest['%D'],
    }
def calculate_stochastic_oscillator_func():
    desc = "Calculate the Stochastic Oscillator (%K and %D) for a given ticker symbol."
    params = {
        'k_period': "period for %K calculation, type: int, default: 14",
        'd_period': "period for %D calculation, type: int, default: 3",
    }
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(calculate_stochastic_oscillator, desc, params, context_params)


def calculate_bollinger_bands(ticker: str, window: int=20, num_std_dev: int=2, date: str="", apikey: str="") -> dict:
    df_daily = fetch_time_series_daily(ticker=ticker, days=window*3, date_to=date, apikey=apikey)
    df_daily = df_daily.sort_values(by='timestamp')  # ascending order for calculation

    df_daily['moving_average'] = df_daily['close'].rolling(window=window).mean()
    df_daily['std_dev'] = df_daily['close'].rolling(window=window).std()
    df_daily['upper_band'] = df_daily['moving_average'] + (df_daily['std_dev'] * num_std_dev)
    df_daily['lower_band'] = df_daily['moving_average'] - (df_daily['std_dev'] * num_std_dev)

    latest = df_daily.iloc[-1]
    return {
        'moving_average': latest['moving_average'],
        'upper_band': latest['upper_band'],
        'lower_band': latest['lower_band'],
    }
def calculate_bollinger_bands_func():
    desc = "Calculate the Bollinger Bands for a given ticker symbol."
    params = {
        'window': "moving average window size, type: int, default: 20",
        'num_std_dev': "number of standard deviations for the bands, type: int, default: 2",
    }
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(calculate_bollinger_bands, desc, params, context_params)


def calculate_atr(ticker: str, period: int=14, date: str="", apikey: str="") -> float:
    df_daily = fetch_time_series_daily(ticker=ticker, days=period*3, date_to=date, apikey=apikey)
    df_daily = df_daily.sort_values(by='timestamp')  # ascending order for calculation

    df_daily['tr'] = pd.concat([
        df_daily['high'] - df_daily['low'],
        abs(df_daily['high'] - df_daily['close'].shift(1)),
        abs(df_daily['low'] - df_daily['close'].shift(1))
    ], axis=1).max(axis=1)

    df_daily['atr'] = df_daily['tr'].rolling(window=period).mean()

    latest = df_daily.iloc[-1]
    return {
        'atr': latest['atr'],
    }
def calculate_atr_func():
    desc = "Calculate the Average True Range (ATR) for a given ticker symbol."
    params = {
        'period': "period for ATR calculation, type: int, default: 14",
    }
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(calculate_atr, desc, params, context_params)


def check_moving_average_crossover(ticker: str, short_window: int=50, long_window: int=200, date: str="", apikey: str="") -> dict:
    df_daily = fetch_time_series_daily(ticker=ticker, days=long_window + 10, date_to=date, apikey=apikey)
    df_daily = df_daily.sort_values(by='timestamp')  # ascending order for calculation

    df_daily['ma_short'] = df_daily['close'].rolling(window=short_window).mean()
    df_daily['ma_long'] = df_daily['close'].rolling(window=long_window).mean()

    latest = df_daily.iloc[-1]
    previous = df_daily.iloc[-2]

    crossover = None
    if previous['ma_short'] < previous['ma_long'] and latest['ma_short'] > latest['ma_long']:
        crossover = "golden_cross"
    elif previous['ma_short'] > previous['ma_long'] and latest['ma_short'] < latest['ma_long']:
        crossover = "death_cross"

    return {
        'crossover': crossover,
        'ma_short': latest['ma_short'],
        'ma_long': latest['ma_long'],
    }
def check_moving_average_crossover_func():
    desc = "Check for moving average crossover (golden cross or death cross) for a given ticker symbol."
    params = {
        'short_window': "short-term moving average window size, type: int, default: 50",
        'long_window': "long-term moving average window size, type: int, default: 200",
    }
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(check_moving_average_crossover, desc, params, context_params)


def find_support_resistance_levels(ticker: str, weeks: int=12, date: str="", apikey: str="") -> dict:
    df_weekly = fetch_time_series_weekly(ticker=ticker, weeks=weeks, date_to=date, apikey=apikey)
    df_weekly = df_weekly.sort_values(by='timestamp')  # ascending order for calculation
    support = df_weekly['low'].min()
    resistance = df_weekly['high'].max()
    return {
        'support_level': support,
        'resistance_level': resistance,
    }
def find_support_resistance_levels_func():
    desc = "Find support and resistance levels over a specified number of weeks for a given ticker symbol."
    params = {
        'weeks': "number of weeks to look back, type: int, default: 12",
    }
    context_params = {
        'ticker': 'ticker',
        'date': 'date',
        'apikey': 'apikey',
    }
    return _get_func_dict(find_support_resistance_levels, desc, params, context_params)

FINANCIAL_TOOLS.extend([
    get_latest_qoute_func(), get_price_summary_for_date_func(), get_price_summary_for_week_func(),
    get_price_summary_for_month_func(), get_historical_highs_lows_func(), calculate_moving_average_func(),
    calculate_macd_func(), calculate_adx_func(), calculate_rsi_func(),
    calculate_stochastic_oscillator_func(), calculate_bollinger_bands_func(), calculate_atr_func(),
    check_moving_average_crossover_func(), find_support_resistance_levels_func(),
])