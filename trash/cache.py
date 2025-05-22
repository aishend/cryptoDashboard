import os
import pandas as pd
from datetime import timedelta
from binance_client import get_futures_klines  # Função que faz a requisição real

CACHE_DIR = "/home/leandro/project/cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cache_filename(symbol, interval):
    return os.path.join(CACHE_DIR, f"{symbol}_{interval}.csv")

def load_cached_data(symbol, interval):
    cache_file = get_cache_filename(symbol, interval)
    if os.path.exists(cache_file):
        df = pd.read_csv(cache_file, index_col="Time", parse_dates=True)
        # Garantir que o índice seja do tipo DatetimeIndex
        df.index = pd.to_datetime(df.index)
        return df
    return pd.DataFrame()

def save_cached_data(symbol, interval, df):
    cache_file = get_cache_filename(symbol, interval)
    df.to_csv(cache_file)

import re

def parse_lookback(lookback):
    """
    Converte uma string como "30 day ago UTC" em um pd.Timedelta.
    Se a string contiver "ago", extrai o número de dias.
    """
    if isinstance(lookback, str) and "ago" in lookback.lower():
        match = re.search(r"(\d+)\s*day", lookback.lower())
        if match:
            days = int(match.group(1))
            return pd.Timedelta(days=days)
        else:
            raise ValueError(f"Não foi possível interpretar a string lookback: {lookback}")
    else:
        return pd.Timedelta(lookback)

def get_klines_with_cache(symbol, interval, lookback):
    """
    Obtém dados de velas (OHLCV) usando cache para Futures ou Spot.
    """
    df_cached = load_cached_data(symbol, interval)
    now = pd.Timestamp.now(tz='UTC')

    # Adiciona suporte para os timeframes "4h", "1h" e "1d"
    INTERVAL_DELTA = {
        "4h": pd.Timedelta(hours=4),
        "1h": pd.Timedelta(hours=1),
        "1d": pd.Timedelta(days=1)
    }

    if not df_cached.empty:
        last_cached_time = df_cached.index.max()
        if last_cached_time.tzinfo is None:
            last_cached_time = last_cached_time.tz_localize('UTC')

        next_expected_time = last_cached_time + INTERVAL_DELTA[interval]
        
        if next_expected_time > now:
            return df_cached
        
        new_start_timestamp = int(next_expected_time.timestamp() * 1000)
        df_new = get_futures_klines(symbol, interval, new_start_timestamp)
        
        if not df_new.empty:
            df_complete = pd.concat([df_cached, df_new]).drop_duplicates().sort_index()
            save_cached_data(symbol, interval, df_complete)
            return df_complete
        return df_cached
    else:
        # Converte o lookback utilizando a função parse_lookback
        lookback_delta = parse_lookback(lookback)
        lookback_time = pd.Timestamp.now(tz='UTC') - lookback_delta
        start_timestamp = int(lookback_time.timestamp() * 1000)

        df_full = get_futures_klines(symbol, interval, start_timestamp)
        if not df_full.empty:
            save_cached_data(symbol, interval, df_full)
        return df_full
