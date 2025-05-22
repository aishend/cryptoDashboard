import streamlit as st
import pandas as pd
import logging

from analysis import analyze_timeframe
from trading_pairs import TRADING_PAIRS
from color_conditions import rsi_color

logging.basicConfig(level=logging.INFO)

st.set_page_config(layout="wide")
st.title("Varredura Interativa de Pares com Filtros Dinâmicos e Cache")
st.markdown("Dev by aishend feat chatgpt")

# Função auxiliar para converter valor do histograma em emoji (bola colorida)
def ball_from_hist(hist):
    if hist > 0:
        return "🟢"
    elif hist < 0:
        return "🔴"
    else:
        return "⚪"

# Função que faz a varredura completa dos pares para os timeframes 1h, 4h e 1d
def scan_pairs():
    valid_pairs = []
    failed_pairs = []
    for symbol in TRADING_PAIRS:
        # Timeframe 1h
        df_1h = analyze_timeframe(symbol, "1h", "7 day ago UTC", prefix="1h_")
        if df_1h.empty or len(df_1h) < 2:
            failed_pairs.append(symbol)
            continue

        # Timeframe 4h
        df_4h = analyze_timeframe(symbol, "4h", "30 day ago UTC", prefix="4h_")
        if df_4h.empty or len(df_4h) < 2:
            failed_pairs.append(symbol)
            continue

        # Timeframe 1d
        df_1d = analyze_timeframe(symbol, "1d", "60 day ago UTC", prefix="1d_")
        if df_1d.empty or len(df_1d) < 2:
            failed_pairs.append(symbol)
            continue

        # Última barra de cada timeframe
        last_1h = df_1h.iloc[-1]
        last_4h = df_4h.iloc[-1]
        last_1d = df_1d.iloc[-1]

        # Indicadores 1h
        rsi_1h = last_1h["1h_rsi"]
        stoch_rsi_1h = last_1h["1h_k"]
        macd_hist_1h = last_1h["1h_macd_hist"]
        macd_zl_hist_1h = last_1h["1h_macd_zero_lag_hist"]
        stoch_1h = last_1h["1h_stoch"]
        stoch_d_1h = last_1h["1h_stoch_d"]

        # Indicadores 4h
        rsi_4h = last_4h["4h_rsi"]
        stoch_rsi_4h = last_4h["4h_k"]
        macd_hist_4h = last_4h["4h_macd_hist"]
        macd_zl_hist_4h = last_4h["4h_macd_zero_lag_hist"]
        stoch_4h = last_4h["4h_stoch"]
        stoch_d_4h = last_4h["4h_stoch_d"]

        # Indicadores 1d
        rsi_1d = last_1d["1d_rsi"]
        stoch_rsi_1d = last_1d["1d_k"]
        macd_hist_1d = last_1d["1d_macd_hist"]
        macd_zl_hist_1d = last_1d["1d_macd_zero_lag_hist"]
        stoch_1d = last_1d["1d_stoch"]
        stoch_d_1d = last_1d["1d_stoch_d"]

        # Emojis para MACD em cada timeframe
        macd_1h_emoji = ball_from_hist(macd_hist_1h)
        macd_zl_1h_emoji = ball_from_hist(macd_zl_hist_1h)
        macd_4h_emoji = ball_from_hist(macd_hist_4h)
        macd_zl_4h_emoji = ball_from_hist(macd_zl_hist_4h)
        macd_1d_emoji = ball_from_hist(macd_hist_1d)
        macd_zl_1d_emoji = ball_from_hist(macd_zl_hist_1d)

        # Verifica se os MACD são invertidos em cada timeframe
        macd_inverted_1h = ((macd_1h_emoji == "🟢" and macd_zl_1h_emoji == "🔴") or 
                            (macd_1h_emoji == "🔴" and macd_zl_1h_emoji == "🟢"))
        macd_inverted_4h = ((macd_4h_emoji == "🟢" and macd_zl_4h_emoji == "🔴") or 
                            (macd_4h_emoji == "🔴" and macd_zl_4h_emoji == "🟢"))
        macd_inverted_1d = ((macd_1d_emoji == "🟢" and macd_zl_1d_emoji == "🔴") or 
                            (macd_1d_emoji == "🔴" and macd_zl_1d_emoji == "🟢"))

        valid_pairs.append({
            "Symbol": symbol,
            # Indicadores 1h
            "1h RSI": round(rsi_1h, 2),
            "1h Stoch RSI": round(stoch_rsi_1h, 2),
            "1h MACD": macd_1h_emoji,
            "1h MACD Zero Lag": macd_zl_1h_emoji,
            "1h MACD Inverted": macd_inverted_1h,
            "1h Stoch": round(stoch_1h, 2),
            "1h Stoch D": round(stoch_d_1h, 2),
            # Indicadores 4h
            "4h RSI": round(rsi_4h, 2),
            "4h Stoch RSI": round(stoch_rsi_4h, 2),
            "4h MACD": macd_4h_emoji,
            "4h MACD Zero Lag": macd_zl_4h_emoji,
            "4h MACD Inverted": macd_inverted_4h,
            "4h Stoch": round(stoch_4h, 2),
            "4h Stoch D": round(stoch_d_4h, 2),
            # Indicadores 1d
            "1d RSI": round(rsi_1d, 2),
            "1d Stoch RSI": round(stoch_rsi_1d, 2),
            "1d MACD": macd_1d_emoji,
            "1d MACD Zero Lag": macd_zl_1d_emoji,
            "1d MACD Inverted": macd_inverted_1d,
            "1d Stoch": round(stoch_1d, 2),
            "1d Stoch D": round(stoch_d_1d, 2),
        })
    return pd.DataFrame(valid_pairs), failed_pairs

@st.cache_data(show_spinner=True)
def get_scan_results():
    return scan_pairs()

if st.sidebar.button("Recarregar Dados"):
    get_scan_results.clear()

df_valid, failed = get_scan_results()

# ------------------------------------------------------------
# Filtros na Sidebar – ORDEM: 1h, 4h, 1d
# ------------------------------------------------------------

# Filtro MACD vs MACD Zero Lag invertidos
st.sidebar.header("Filtro MACD vs MACD Zero Lag invertidos")
filter_macd_inverted_1h = st.sidebar.checkbox("Inversão no 1h", key="filter_macd_inverted_1h")
filter_macd_inverted_4h = st.sidebar.checkbox("Inversão no 4h")
filter_macd_inverted_1d = st.sidebar.checkbox("Inversão no 1d")

# Filtro Stoch RSI
st.sidebar.header("Filtro Stoch RSI - 1h")
stoch_mode_1h = st.sidebar.radio("Modo de filtro 1h:", ["Nenhum", "Limite inferior", "Limite superior", "Ambos"], index=0, key="stoch_mode_1h")
if stoch_mode_1h in ["Limite inferior", "Ambos"]:
    stoch_lower_1h = st.sidebar.number_input("1h Stoch RSI - Limite Inferior", min_value=0, max_value=100, value=20, key="stoch_lower_1h")
if stoch_mode_1h in ["Limite superior", "Ambos"]:
    stoch_upper_1h = st.sidebar.number_input("1h Stoch RSI - Limite Superior", min_value=0, max_value=100, value=80, key="stoch_upper_1h")

st.sidebar.header("Filtro Stoch RSI - 4h")
stoch_mode_4h = st.sidebar.radio("Modo de filtro 4h:", ["Nenhum", "Limite inferior", "Limite superior", "Ambos"], index=0, key="stoch_mode_4h")
if stoch_mode_4h in ["Limite inferior", "Ambos"]:
    stoch_lower_4h = st.sidebar.number_input("4h Stoch RSI - Limite Inferior", min_value=0, max_value=100, value=20, key="stoch_lower_4h")
if stoch_mode_4h in ["Limite superior", "Ambos"]:
    stoch_upper_4h = st.sidebar.number_input("4h Stoch RSI - Limite Superior", min_value=0, max_value=100, value=80, key="stoch_upper_4h")

st.sidebar.header("Filtro Stoch RSI - 1d")
stoch_mode_1d = st.sidebar.radio("Modo de filtro 1d:", ["Nenhum", "Limite inferior", "Limite superior", "Ambos"], index=0, key="stoch_mode_1d")
if stoch_mode_1d in ["Limite inferior", "Ambos"]:
    stoch_lower_1d = st.sidebar.number_input("1d Stoch RSI - Limite Inferior", min_value=0, max_value=100, value=20, key="stoch_lower_1d")
if stoch_mode_1d in ["Limite superior", "Ambos"]:
    stoch_upper_1d = st.sidebar.number_input("1d Stoch RSI - Limite Superior", min_value=0, max_value=100, value=80, key="stoch_upper_1d")

# Filtro RSI
st.sidebar.header("Filtro RSI - 1h")
rsi_mode_1h = st.sidebar.radio("Modo de filtro 1h:", ["Nenhum", "Limite inferior", "Limite superior", "Ambos"], index=0, key="rsi_mode_1h")
if rsi_mode_1h in ["Limite inferior", "Ambos"]:
    rsi_lower_1h = st.sidebar.number_input("1h RSI - Limite Inferior", min_value=0, max_value=100, value=30, key="rsi_lower_1h")
if rsi_mode_1h in ["Limite superior", "Ambos"]:
    rsi_upper_1h = st.sidebar.number_input("1h RSI - Limite Superior", min_value=0, max_value=100, value=70, key="rsi_upper_1h")

st.sidebar.header("Filtro RSI - 4h")
rsi_mode_4h = st.sidebar.radio("Modo de filtro 4h:", ["Nenhum", "Limite inferior", "Limite superior", "Ambos"], index=0, key="rsi_mode_4h")
if rsi_mode_4h in ["Limite inferior", "Ambos"]:
    rsi_lower_4h = st.sidebar.number_input("4h RSI - Limite Inferior", min_value=0, max_value=100, value=30, key="rsi_lower_4h")
if rsi_mode_4h in ["Limite superior", "Ambos"]:
    rsi_upper_4h = st.sidebar.number_input("4h RSI - Limite Superior", min_value=0, max_value=100, value=70, key="rsi_upper_4h")

st.sidebar.header("Filtro RSI - 1d")
rsi_mode_1d = st.sidebar.radio("Modo de filtro 1d:", ["Nenhum", "Limite inferior", "Limite superior", "Ambos"], index=0, key="rsi_mode_1d")
if rsi_mode_1d in ["Limite inferior", "Ambos"]:
    rsi_lower_1d = st.sidebar.number_input("1d RSI - Limite Inferior", min_value=0, max_value=100, value=30, key="rsi_lower_1d")
if rsi_mode_1d in ["Limite superior", "Ambos"]:
    rsi_upper_1d = st.sidebar.number_input("1d RSI - Limite Superior", min_value=0, max_value=100, value=70, key="rsi_upper_1d")

# Filtro do novo indicador Stochastic (Pine) – Ordem: 1h, 4h, 1d
st.sidebar.header("Filtro Stoch (Indicador Pine) - 1h")
stoch_val_mode_1h = st.sidebar.radio("Modo de filtro 1h:", ["Nenhum", "Limite inferior", "Limite superior", "Ambos"], index=0, key="stoch_val_mode_1h")
if stoch_val_mode_1h in ["Limite inferior", "Ambos"]:
    stoch_val_lower_1h = st.sidebar.number_input("1h Stoch - Limite Inferior", min_value=0, max_value=100, value=30, key="stoch_val_lower_1h")
if stoch_val_mode_1h in ["Limite superior", "Ambos"]:
    stoch_val_upper_1h = st.sidebar.number_input("1h Stoch - Limite Superior", min_value=0, max_value=100, value=70, key="stoch_val_upper_1h")

st.sidebar.header("Filtro Stoch (Indicador Pine) - 4h")
stoch_val_mode_4h = st.sidebar.radio("Modo de filtro 4h:", ["Nenhum", "Limite inferior", "Limite superior", "Ambos"], index=0, key="stoch_val_mode_4h")
if stoch_val_mode_4h in ["Limite inferior", "Ambos"]:
    stoch_val_lower_4h = st.sidebar.number_input("4h Stoch - Limite Inferior", min_value=0, max_value=100, value=30, key="stoch_val_lower_4h")
if stoch_val_mode_4h in ["Limite superior", "Ambos"]:
    stoch_val_upper_4h = st.sidebar.number_input("4h Stoch - Limite Superior", min_value=0, max_value=100, value=70, key="stoch_val_upper_4h")

st.sidebar.header("Filtro Stoch (Indicador Pine) - 1d")
stoch_val_mode_1d = st.sidebar.radio("Modo de filtro 1d:", ["Nenhum", "Limite inferior", "Limite superior", "Ambos"], index=0, key="stoch_val_mode_1d")
if stoch_val_mode_1d in ["Limite inferior", "Ambos"]:
    stoch_val_lower_1d = st.sidebar.number_input("1d Stoch - Limite Inferior", min_value=0, max_value=100, value=30, key="stoch_val_lower_1d")
if stoch_val_mode_1d in ["Limite superior", "Ambos"]:
    stoch_val_upper_1d = st.sidebar.number_input("1d Stoch - Limite Superior", min_value=0, max_value=100, value=70, key="stoch_val_upper_1d")

# ------------------------------------------------------------
# Aplicando os filtros no DataFrame dos pares
# ------------------------------------------------------------
df_filtered = df_valid.copy()

if filter_macd_inverted_1h:
    df_filtered = df_filtered[df_filtered["1h MACD Inverted"] == True]
if filter_macd_inverted_4h:
    df_filtered = df_filtered[df_filtered["4h MACD Inverted"] == True]
if filter_macd_inverted_1d:
    df_filtered = df_filtered[df_filtered["1d MACD Inverted"] == True]

if stoch_mode_1h == "Limite inferior":
    df_filtered = df_filtered[df_filtered["1h Stoch RSI"] < stoch_lower_1h]
elif stoch_mode_1h == "Limite superior":
    df_filtered = df_filtered[df_filtered["1h Stoch RSI"] > stoch_upper_1h]
elif stoch_mode_1h == "Ambos":
    df_filtered = df_filtered[(df_filtered["1h Stoch RSI"] < stoch_lower_1h) | (df_filtered["1h Stoch RSI"] > stoch_upper_1h)]

if stoch_mode_4h == "Limite inferior":
    df_filtered = df_filtered[df_filtered["4h Stoch RSI"] < stoch_lower_4h]
elif stoch_mode_4h == "Limite superior":
    df_filtered = df_filtered[df_filtered["4h Stoch RSI"] > stoch_upper_4h]
elif stoch_mode_4h == "Ambos":
    df_filtered = df_filtered[(df_filtered["4h Stoch RSI"] < stoch_lower_4h) | (df_filtered["4h Stoch RSI"] > stoch_upper_4h)]

if stoch_mode_1d == "Limite inferior":
    df_filtered = df_filtered[df_filtered["1d Stoch RSI"] < stoch_lower_1d]
elif stoch_mode_1d == "Limite superior":
    df_filtered = df_filtered[df_filtered["1d Stoch RSI"] > stoch_upper_1d]
elif stoch_mode_1d == "Ambos":
    df_filtered = df_filtered[(df_filtered["1d Stoch RSI"] < stoch_lower_1d) | (df_filtered["1d Stoch RSI"] > stoch_upper_1d)]

if rsi_mode_1h == "Limite inferior":
    df_filtered = df_filtered[df_filtered["1h RSI"] < rsi_lower_1h]
elif rsi_mode_1h == "Limite superior":
    df_filtered = df_filtered[df_filtered["1h RSI"] > rsi_upper_1h]
elif rsi_mode_1h == "Ambos":
    df_filtered = df_filtered[(df_filtered["1h RSI"] < rsi_lower_1h) | (df_filtered["1h RSI"] > rsi_upper_1h)]

if rsi_mode_4h == "Limite inferior":
    df_filtered = df_filtered[df_filtered["4h RSI"] < rsi_lower_4h]
elif rsi_mode_4h == "Limite superior":
    df_filtered = df_filtered[df_filtered["4h RSI"] > rsi_upper_4h]
elif rsi_mode_4h == "Ambos":
    df_filtered = df_filtered[(df_filtered["4h RSI"] < rsi_lower_4h) | (df_filtered["4h RSI"] > rsi_upper_4h)]

if rsi_mode_1d == "Limite inferior":
    df_filtered = df_filtered[df_filtered["1d RSI"] < rsi_lower_1d]
elif rsi_mode_1d == "Limite superior":
    df_filtered = df_filtered[df_filtered["1d RSI"] > rsi_upper_1d]
elif rsi_mode_1d == "Ambos":
    df_filtered = df_filtered[(df_filtered["1d RSI"] < rsi_lower_1d) | (df_filtered["1d RSI"] > rsi_upper_1d)]

if stoch_val_mode_1h == "Limite inferior":
    df_filtered = df_filtered[df_filtered["1h Stoch"] < stoch_val_lower_1h]
elif stoch_val_mode_1h == "Limite superior":
    df_filtered = df_filtered[df_filtered["1h Stoch"] > stoch_val_upper_1h]
elif stoch_val_mode_1h == "Ambos":
    df_filtered = df_filtered[(df_filtered["1h Stoch"] < stoch_val_lower_1h) | (df_filtered["1h Stoch"] > stoch_val_upper_1h)]

if stoch_val_mode_4h == "Limite inferior":
    df_filtered = df_filtered[df_filtered["4h Stoch"] < stoch_val_lower_4h]
elif stoch_val_mode_4h == "Limite superior":
    df_filtered = df_filtered[df_filtered["4h Stoch"] > stoch_val_upper_4h]
elif stoch_val_mode_4h == "Ambos":
    df_filtered = df_filtered[(df_filtered["4h Stoch"] < stoch_val_lower_4h) | (df_filtered["4h Stoch"] > stoch_val_upper_4h)]

if stoch_val_mode_1d == "Limite inferior":
    df_filtered = df_filtered[df_filtered["1d Stoch"] < stoch_val_lower_1d]
elif stoch_val_mode_1d == "Limite superior":
    df_filtered = df_filtered[df_filtered["1d Stoch"] > stoch_val_upper_1d]
elif stoch_val_mode_1d == "Ambos":
    df_filtered = df_filtered[(df_filtered["1d Stoch"] < stoch_val_lower_1d) | (df_filtered["1d Stoch"] > stoch_val_upper_1d)]

# Opcional: remover as colunas de inversão se não quiser exibi-las
df_filtered = df_filtered.drop(columns=["1h MACD Inverted", "4h MACD Inverted", "1d MACD Inverted"], errors='ignore')

with st.spinner("Aplicando filtros..."):
    if not df_filtered.empty:
        st.subheader("Pares que atendem aos filtros:")
        st.table(df_filtered)
    else:
        st.write("Nenhum par atendeu aos filtros selecionados.")

if failed:
    st.subheader("Pares sem dados suficientes ou com erros:")
    for symbol in failed:
        st.write(symbol)
