import streamlit as st
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import logging

from analysis import analyze_timeframe
from trading_pairs import TRADING_PAIRS

logging.basicConfig(level=logging.INFO)

st.set_page_config(layout="wide")
st.title("Varredura Interativa de Pares – Apenas Stochastic (1h & 4h)")
st.markdown("Dev by aishend feat chatgpt — versão só Stochastic 5-3-3 & 14-3-3 ☕️")

# ------------------------------------------------------------
# Função tradicional de cálculo (para verificação)
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Varredura dos pares
# ------------------------------------------------------------
def scan_pairs():
    valid_rows = []
    failed_pairs = []
    for symbol in TRADING_PAIRS:
        try:
            df_1h = analyze_timeframe(symbol, "1h", "7 day ago UTC")
            df_4h = analyze_timeframe(symbol, "4h", "30 day ago UTC")
            if df_1h.empty or df_4h.empty:
                failed_pairs.append(symbol)
                continue
            # calcula stoch
            for df, tf in ((df_1h, "1h"), (df_4h, "4h")):
                _calc_stoch(df, 5, 3, 3, f"{tf}_5")
                _calc_stoch(df, 14, 3, 3, f"{tf}_14")
            last_1h = df_1h.iloc[-1]
            last_4h = df_4h.iloc[-1]
            valid_rows.append({
                "Symbol": symbol,
                "1h Stoch 5-3-3": round(last_1h["1h_5_stoch_5"], 2),
                "1h Stoch 14-3-3": round(last_1h["1h_14_stoch_14"], 2),
                "4h Stoch 5-3-3": round(last_4h["4h_5_stoch_5"], 2),
                "4h Stoch 14-3-3": round(last_4h["4h_14_stoch_14"], 2),
            })
        except Exception as exc:
            logging.warning(f"Falha ao processar {symbol}: {exc}")
            failed_pairs.append(symbol)
    return pd.DataFrame(valid_rows), failed_pairs

# ------------------------------------------------------------
# Cache
# ------------------------------------------------------------
@st.cache_data(show_spinner=True, ttl=1800)
def get_scan_results():
    results = scan_pairs()
    # Armazena o timestamp atual junto com os resultados
    return results, pd.Timestamp.now()

# Obter resultados e timestamp
(df_valid, failed), last_update_time = get_scan_results()

# Exibir informação de última atualização
st.sidebar.info(f"Última atualização: {last_update_time.strftime('%H:%M:%S')}")

if st.sidebar.button("Atualizar Agora"):
    get_scan_results.clear()
    st.rerun()

# ------------------------------------------------------------
# Escolha de Símbolo para plot
# ------------------------------------------------------------
st.sidebar.header("Visualizar Stochastic Histórico")
symbol_plot = st.sidebar.selectbox("Selecione par:", TRADING_PAIRS)

# ------------------------------------------------------------
# Filtros Stochastic
# ------------------------------------------------------------
st.sidebar.header("Filtros Stochastic")
filters = {}
for col_key, col_label in [
    ("1h Stoch 5-3-3", "1h 5-3-3"),
    ("1h Stoch 14-3-3", "1h 14-3-3"),
    ("4h Stoch 5-3-3", "4h 5-3-3"),
    ("4h Stoch 14-3-3", "4h 14-3-3"),
]:
    mode = st.sidebar.radio(col_label + ":", ["Nenhum", "Inferior", "Superior", "Ambos"], key=col_key)
    low = st.sidebar.number_input(f"{col_label} – Inferior", 0, 100, 30, key="low_"+col_key) if mode in ["Inferior", "Ambos"] else None
    up  = st.sidebar.number_input(f"{col_label} – Superior", 0, 100, 70, key="up_"+col_key)  if mode in ["Superior", "Ambos"] else None
    filters[col_key] = (mode, low, up)

# ------------------------------------------------------------
# Exibição de Tabela
# ------------------------------------------------------------
df_valid, failed = get_scan_results()
df_filtered = df_valid.copy()
for column, (mode, low, up) in filters.items():
    if mode == "Inferior": df_filtered = df_filtered[df_filtered[column] < low]
    if mode == "Superior": df_filtered = df_filtered[df_filtered[column] > up]
    if mode == "Ambos":    df_filtered = df_filtered[(df_filtered[column] < low)|(df_filtered[column] > up)]
if df_filtered.empty:
    st.write("Nenhum par atende aos filtros.")
else:
    st.subheader("Pares Filtrados")
    st.table(df_filtered)
if failed:
    st.subheader("Erros ao carregar")
    for s in failed: st.write(s)
