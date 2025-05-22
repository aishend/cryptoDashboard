import streamlit as st
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import logging
import time
from datetime import datetime, timedelta

from analysis import analyze_timeframe
from trading_pairs import TRADING_PAIRS

logging.basicConfig(level=logging.INFO)

st.set_page_config(layout="wide")

# Auto-refresh JavaScript
st.markdown("""
<script>
setTimeout(function(){
    window.location.reload(1);
}, 1800000); // 30 minutos
</script>
""", unsafe_allow_html=True)

st.title("Varredura Interativa de Pares – Apenas Stochastic (1h & 4h)")
st.markdown("Dev by aishend feat chatgpt — versão só Stochastic 5-3-3 & 14-3-3 ☕️")


# ------------------------------------------------------------
# Funções (mantém as suas originais)
# ------------------------------------------------------------
def calc_stochastic_indicator(df, periodK, smoothK, periodD):
    lowest_low = df['Low'].rolling(window=periodK).min()
    highest_high = df['High'].rolling(window=periodK).max()
    stoch = 100 * (df['Close'] - lowest_low) / (highest_high - lowest_low)
    stoch_K = stoch.rolling(window=smoothK).mean()
    stoch_D = stoch_K.rolling(window=periodD).mean()
    return stoch_K, stoch_D


def _calc_stoch(df: pd.DataFrame, k: int, d: int, smooth_k: int, label_prefix: str):
    if not all(col in df.columns for col in ["High", "Low", "Close"]):
        raise KeyError(f"DataFrame sem colunas necessárias, colunas: {df.columns.tolist()}")
    stoch = ta.stoch(df["High"], df["Low"], df["Close"], k=k, d=d, smooth_k=smooth_k)
    df[f"{label_prefix}_stoch_{k}"] = stoch.iloc[:, 0]
    return df


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
# Cache com cronômetro
# ------------------------------------------------------------
@st.cache_data(show_spinner=True, ttl=1800)
def get_scan_results():
    return scan_pairs(), datetime.now()


# Placeholder para cronômetro
timer_placeholder = st.sidebar.empty()
status_placeholder = st.sidebar.empty()

# ------------------------------------------------------------
# Obter e exibir resultados
# ------------------------------------------------------------
(df_valid, failed), last_update_time = get_scan_results()

# Debug - mostrar dados brutos
st.write("🔍 **Debug Info:**")
st.write(f"- Pares válidos: {len(df_valid)}")
st.write(f"- Pares com erro: {len(failed)}")

if not df_valid.empty:
    st.write("- Primeiros dados:")
    st.dataframe(df_valid.head())

# Aplicar filtros APENAS se não for "Nenhum"
df_filtered = df_valid.copy()

for column, (mode, low, up) in filters.items():
    if mode == "Inferior" and low is not None:
        df_filtered = df_filtered[df_filtered[column] < low]
        st.write(f"Filtro aplicado: {column} < {low}")
    elif mode == "Superior" and up is not None:
        df_filtered = df_filtered[df_filtered[column] > up]
        st.write(f"Filtro aplicado: {column} > {up}")
    elif mode == "Ambos" and low is not None and up is not None:
        df_filtered = df_filtered[(df_filtered[column] < low) | (df_filtered[column] > up)]
        st.write(f"Filtro aplicado: {column} < {low} OU > {up}")

st.write(f"📊 **Dados após filtros: {len(df_filtered)} pares**")

# Exibir resultados
if df_filtered.empty:
    if df_valid.empty:
        st.error("❌ Nenhum dado foi carregado. Verifique a conexão com a API.")
    else:
        st.warning("⚠️ Nenhum par atende aos filtros aplicados.")
        st.write("Dados disponíveis antes dos filtros:")
        st.dataframe(df_valid)
else:
    st.subheader("✅ Pares Filtrados")
    st.dataframe(df_filtered, use_container_width=True)

# Mostrar erros se houver
if failed:
    st.subheader("❌ Erros ao carregar")
    st.error(f"Falha ao carregar {len(failed)} pares:")
    for s in failed:
        st.write(f"- {s}")
