import streamlit as st
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import logging
import json
from datetime import datetime, timedelta
import os

from analysis import analyze_timeframe
from trading_pairs import TRADING_PAIRS

logging.basicConfig(level=logging.INFO)

st.set_page_config(layout="wide")
st.title("Varredura Interativa de Pares – Apenas Stochastic (1h & 4h)")
st.markdown("Dev by aishend feat chatgpt — versão só Stochastic 5-3-3 & 14-3-3 ☕️")


# ------------------------------------------------------------
# Funções originais
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
# Funções de cache com arquivo JSON
# ------------------------------------------------------------
def save_data_to_file(df_valid, failed):
    """Salva dados em arquivo JSON"""
    data = {
        'df_valid': df_valid.to_dict('records') if not df_valid.empty else [],
        'failed': failed,
        'last_update': datetime.now().isoformat()
    }

    with open('crypto_data.json', 'w') as f:
        json.dump(data, f, indent=2)


def load_data_from_file():
    """Carrega dados do arquivo JSON"""
    try:
        if os.path.exists('crypto_data.json'):
            with open('crypto_data.json', 'r') as f:
                data = json.load(f)

            df_valid = pd.DataFrame(data['df_valid']) if data['df_valid'] else pd.DataFrame()
            failed = data['failed']
            last_update = datetime.fromisoformat(data['last_update'])

            return df_valid, failed, last_update
        else:
            # Se arquivo não existe, criar dados iniciais
            return pd.DataFrame(), [], datetime.now()
    except Exception as e:
        logging.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), [], datetime.now()


@st.cache_data(ttl=60)  # Cache por 1 minuto
def get_scan_results():
    """Carrega dados do arquivo ou busca novos se necessário"""
    df_valid, failed, last_update = load_data_from_file()

    # Se dados são muito antigos (mais de 35 minutos), buscar novos
    if (datetime.now() - last_update).total_seconds() > 2100:
        try:
            df_valid, failed = scan_pairs()
            save_data_to_file(df_valid, failed)
            last_update = datetime.now()
        except Exception as e:
            logging.error(f"Erro ao buscar novos dados: {e}")

    return df_valid, failed, last_update


def force_update():
    """Força atualização dos dados"""
    try:
        df_valid, failed = scan_pairs()
        save_data_to_file(df_valid, failed)
        return df_valid, failed, datetime.now()
    except Exception as e:
        logging.error(f"Erro na atualização forçada: {e}")
        return load_data_from_file()


# ------------------------------------------------------------
# Obter dados
# ------------------------------------------------------------
df_valid, failed, last_update_time = get_scan_results()

# Calcular tempo para próxima atualização
next_update = last_update_time + timedelta(seconds=1800)  # 30 minutos
time_remaining = next_update - datetime.now()

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
st.sidebar.header("⏱️ Status")
st.sidebar.info(f"Última atualização: {last_update_time.strftime('%H:%M:%S')}")

if time_remaining.total_seconds() > 0:
    minutes = int(time_remaining.total_seconds() // 60)
    seconds = int(time_remaining.total_seconds() % 60)
    st.sidebar.success(f"Próxima atualização em: {minutes:02d}:{seconds:02d}")
else:
    st.sidebar.warning("Atualização pendente...")

# Botões de controle
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 Atualizar"):
        df_valid, failed, last_update_time = force_update()
        get_scan_results.clear()
        st.rerun()

with col2:
    if st.button("📊 Recarregar"):
        get_scan_results.clear()
        st.rerun()

st.sidebar.divider()

# Escolha de símbolo
st.sidebar.header("📈 Visualização")
symbol_plot = st.sidebar.selectbox("Selecione par:", TRADING_PAIRS)

st.sidebar.divider()

# ------------------------------------------------------------
# Filtros
# ------------------------------------------------------------
st.sidebar.header("🎛️ Filtros Stochastic")
filters = {}

for col_key, col_label in [
    ("1h Stoch 5-3-3", "1h 5-3-3"),
    ("1h Stoch 14-3-3", "1h 14-3-3"),
    ("4h Stoch 5-3-3", "4h 5-3-3"),
    ("4h Stoch 14-3-3", "4h 14-3-3"),
]:
    use_filter = st.sidebar.checkbox(f"Filtrar {col_label}", key=f"use_{col_key}")

    if use_filter:
        filter_type = st.sidebar.radio(
            f"{col_label}:",
            ["Inferior", "Superior", "Ambos"],
            key=f"type_{col_key}"
        )

        if filter_type in ["Inferior", "Ambos"]:
            low = st.sidebar.number_input(f"{col_label} – Inferior", 0, 100, 30, key=f"low_{col_key}")
        else:
            low = None

        if filter_type in ["Superior", "Ambos"]:
            up = st.sidebar.number_input(f"{col_label} – Superior", 0, 100, 70, key=f"up_{col_key}")
        else:
            up = None

        filters[col_key] = (filter_type, low, up)
    else:
        filters[col_key] = ("Nenhum", None, None)

# ------------------------------------------------------------
# Aplicar filtros
# ------------------------------------------------------------
df_filtered = df_valid.copy()

for column, (mode, low, up) in filters.items():
    if mode == "Inferior" and low is not None:
        df_filtered = df_filtered[df_filtered[column] < low]
    elif mode == "Superior" and up is not None:
        df_filtered = df_filtered[df_filtered[column] > up]
    elif mode == "Ambos" and low is not None and up is not None:
        df_filtered = df_filtered[(df_filtered[column] < low) | (df_filtered[column] > up)]

# ------------------------------------------------------------
# Exibir resultados
# ------------------------------------------------------------
if df_filtered.empty:
    if df_valid.empty:
        st.error("❌ Nenhum dado disponível. Clique em 'Atualizar' para buscar dados.")
    else:
        st.warning("⚠️ Nenhum par atende aos filtros aplicados.")
else:
    st.subheader(f"✅ Pares Filtrados ({len(df_filtered)} de {len(df_valid)})")
    st.table(df_filtered)

if failed:
    with st.expander(f"❌ Erros ao carregar ({len(failed)} pares)"):
        for s in failed:
            st.write(f"- {s}")

# Status dos dados
st.sidebar.markdown("---")
st.sidebar.caption(f"📊 {len(df_valid)} pares carregados")
st.sidebar.caption(f"❌ {len(failed)} com erro")
