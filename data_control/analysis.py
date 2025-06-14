try:
    from data_control.cache import get_klines_with_cache  # Função com cache para obter velas
except ImportError:
    from cache import get_klines_with_cache
try:
    from indicators_set.indicators import apply_technicals
except ImportError:
    from indicators import apply_technicals


def analyze_timeframe(symbol, interval, lookback, prefix=""):
    df = get_klines_with_cache(symbol, interval, lookback)
    
    if df.empty:
        print("DataFrame vazio após get_klines_with_cache.")
        return df
    
    # Repassa o timeframe para aplicar os indicadores com os parâmetros corretos
    df = apply_technicals(df, timeframe=interval)
    
    if df.empty:
        return df
    
    if prefix:
        df = df.add_prefix(prefix)
    return df
