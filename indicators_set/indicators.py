# indicators.py
import pandas as pd
import pandas_ta as ta
from indicators_set.indicator_config import INDICATOR_CONFIG

# --------------------------------------------
# 3) Cálculo manual do RSI (Wilders)
# --------------------------------------------
def calc_rsi(series, length=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    alpha = 1 / length
    rma_up = up.ewm(alpha=alpha, adjust=False).mean()
    rma_down = down.ewm(alpha=alpha, adjust=False).mean()
    rsi = 100 - (100 / (1 + (rma_up / rma_down)))
    return rsi

# --------------------------------------------
# 4) Cálculo manual do Stochastic RSI
# --------------------------------------------
def calc_stoch_rsi(rsi, rsi_length=14, k=3, d=3):
    lowest_rsi = rsi.rolling(rsi_length).min()
    highest_rsi = rsi.rolling(rsi_length).max()
    stoch_rsi = 100 * (rsi - lowest_rsi) / (highest_rsi - lowest_rsi)
    stoch_rsi = stoch_rsi.replace([np.inf, -np.inf], np.nan)
    k_line = stoch_rsi.rolling(k).mean()
    d_line = k_line.rolling(d).mean()
    return stoch_rsi, k_line, d_line

# --------------------------------------------
# 5) Cálculo manual do MACD tradicional
# --------------------------------------------
def calc_macd(series, fast_length=12, slow_length=26, signal_length=9):
    ema_fast = series.ewm(span=fast_length, adjust=False).mean()
    ema_slow = series.ewm(span=slow_length, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_length, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist

# --------------------------------------------
# 6) Cálculo do MACD Zero Lag
# Utiliza duas sucessivas EMAs para reduzir o atraso (lag)
# --------------------------------------------
def calc_macd_zero_lag(series, fast_length=12, slow_length=24, signal_length=9):
    ema_fast = series.ewm(span=fast_length, adjust=False).mean()
    ema_fast2 = ema_fast.ewm(span=fast_length, adjust=False).mean()
    diff_fast = ema_fast - ema_fast2
    zlag_fast = ema_fast + diff_fast

    ema_slow = series.ewm(span=slow_length, adjust=False).mean()
    ema_slow2 = ema_slow.ewm(span=slow_length, adjust=False).mean()
    diff_slow = ema_slow - ema_slow2
    zlag_slow = ema_slow + diff_slow

    macd_line = zlag_fast - zlag_slow

    ema_signal = macd_line.ewm(span=signal_length, adjust=False).mean()
    ema_signal2 = ema_signal.ewm(span=signal_length, adjust=False).mean()
    diff_signal = ema_signal - ema_signal2
    signal_line = ema_signal + diff_signal

    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist

# --------------------------------------------
# Novo: Cálculo do indicador Stochastic (baseado no PineScript)
# --------------------------------------------
def calc_stochastic_indicator(df, periodK, smoothK, periodD):
    lowest_low = df['Low'].rolling(window=periodK).min()
    highest_high = df['High'].rolling(window=periodK).max()
    stoch = 100 * (df['Close'] - lowest_low) / (highest_high - lowest_low)
    stoch_K = stoch.rolling(window=smoothK).mean()
    stoch_D = stoch_K.rolling(window=periodD).mean()
    return stoch_K, stoch_D

# ------------------------------------------------------------
# Utilidades pandas_ta
# ------------------------------------------------------------
def _calc_stoch(df: pd.DataFrame, k: int, d: int, smooth_k: int, label_prefix: str):
    if not all(col in df.columns for col in ["High", "Low", "Close"]):
        raise KeyError(f"DataFrame sem colunas necessárias, colunas: {df.columns.tolist()}")
    stoch = ta.stoch(df["High"], df["Low"], df["Close"], k=k, d=d, smooth_k=smooth_k)
    df[f"{label_prefix}_stoch_{k}"] = stoch.iloc[:, 0]
    return df


import numpy as np


def normalize_macd_histogram(hist_values):
    """
    Normaliza o histograma MACD para o intervalo [0, 100], com 50 representando o zero do histograma.
    hist_values: array-like de valores do histograma MACD
    Retorna: array numpy com valores normalizados entre 0 e 100
    """
    hist_values = np.array(hist_values, dtype=float)
    hist_min = np.min(hist_values)
    hist_max = np.max(hist_values)

    # Se hist_min e hist_max forem iguais, retorna array de 50 (meio do range)
    if hist_min == hist_max:
        return np.full(hist_values.shape, 50, dtype=float)

    # Normaliza para [0, 1]
    norm = (hist_values - hist_min) / (hist_max - hist_min)

    # Calcula a posição do zero no range original
    zero_pos = (0 - hist_min) / (hist_max - hist_min)

    # Ajusta para que zero_pos fique em 0.5 (50)
    if zero_pos == 0:
        a = 1
        b = 0
    else:
        a = 0.5 / zero_pos
        b = 0
    norm_adjusted = a * norm + b

    # Limita para [0, 1]
    norm_adjusted = np.clip(norm_adjusted, 0, 1)

    # Escala para [0, 100]
    norm_scaled = norm_adjusted * 100

    return norm_scaled


# --------------------------------------------
# 7) Função que aplica todos os indicadores ao DataFrame
# --------------------------------------------
def apply_technicals(df, timeframe=None):
    # Recupera os parâmetros de configuração para o timeframe especificado.
    config = INDICATOR_CONFIG.get(timeframe, INDICATOR_CONFIG["1h"])

    # RSI
    df['rsi'] = calc_rsi(df['Close'], length=config["RSI"]["length"])
    
    # Stochastic RSI
    stoch_rsi, k_line, d_line = calc_stoch_rsi(
        df['rsi'],
        rsi_length=config["StochRSI"]["rsi_length"],
        k=config["StochRSI"]["k"],
        d=config["StochRSI"]["d"]
    )
    df['stoch_rsi'] = stoch_rsi
    df['k'] = k_line
    df['d'] = d_line
    
    # MACD tradicional
    macd_line, signal_line, macd_hist = calc_macd(
        df['Close'],
        config["MACD"]["fast_length"],
        config["MACD"]["slow_length"],
        config["MACD"]["signal_length"]
    )
    df['macd_line'] = macd_line
    df['signal_line'] = signal_line
    df['macd_hist'] = macd_hist

    # MACD Zero Lag
    macd_zl_line, macd_zl_signal, macd_zl_hist = calc_macd_zero_lag(
        df['Close'],
        fast_length=config["MACDZeroLag"]["fast_length"],
        slow_length=config["MACDZeroLag"]["slow_length"],
        signal_length=config["MACDZeroLag"]["signal_length"]
    )
    df['macd_zero_lag_line'] = macd_zl_line
    df['macd_zero_lag_signal'] = macd_zl_signal
    df['macd_zero_lag_hist'] = macd_zl_hist

    # Indicador Stochastic (estilo PineScript)
    stoch_K, stoch_D = calc_stochastic_indicator(
        df,
        periodK=config["Stochastic"]["periodK"],
        smoothK=config["Stochastic"]["smoothK"],
        periodD=config["Stochastic"]["periodD"]
    )
    df['stoch'] = stoch_K
    df['stoch_d'] = stoch_D

    df.dropna(inplace=True)
    return df
