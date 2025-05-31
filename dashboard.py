import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import numpy as np
import sys
import subprocess

def safe_run_update(script_path):
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            st.info(result.stdout)
    except subprocess.CalledProcessError as e:
        st.error(f"Erro ao rodar {script_path}:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        raise st.stop()

safe_run_update("trading_pairs/update_trading_pairs.py")
safe_run_update("data_control/update_data.py")

st.set_page_config(layout="wide")

count = st_autorefresh(interval=300000, key="filecheck")

st.title("📊 Dashboard Crypto Filtering")
st.markdown("Dev by aishend - Stochastic Version 5-3-3 & 14-3-3 ☕️")

@st.cache_data(ttl=60)
def load_data_from_file():
    try:
        if os.path.exists('data_control/crypto_data.json'):
            with open('data_control/crypto_data.json', 'r') as f:
                data = json.load(f)
            df_valid = pd.DataFrame(data['df_valid'])
            failed = data['failed']
            last_update = datetime.fromisoformat(data['last_update'])
            return df_valid, failed, last_update, True
        else:
            return pd.DataFrame(), [], datetime.now(), False
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), [], datetime.now(), False

df_valid, failed, last_update_time, file_exists = load_data_from_file()

if file_exists:
    st.sidebar.success(f"✅ Dados carregados: {last_update_time.strftime('%H:%M:%S')}")
    time_diff = datetime.now() - last_update_time
    minutes_ago = int(time_diff.total_seconds() / 60)
    st.sidebar.info(f"📅 Atualizado há {minutes_ago} minutos")
else:
    st.sidebar.error("❌ Arquivo de dados não encontrado")

if st.sidebar.button("🔄 Recarregar Dados"):
    load_data_from_file.clear()
    st.rerun()

# ----------------- Seleção de Timeframes para filtro Stochastic -----------------
st.sidebar.header("Timeframes para Filtro")
all_timeframes = []
for tf in ["15m", "1h", "4h", "1d"]:
    if any(col.startswith(f"{tf} Stoch") for col in df_valid.columns):
        all_timeframes.append(tf)

default_timeframes = [tf for tf in ["1h", "4h"] if tf in all_timeframes]
selected_timeframes = st.sidebar.multiselect(
    "Selecione os timeframes para aplicar os filtros:",
    options=all_timeframes,
    default=default_timeframes
)

# ----------------- Filtros Gerais Stochastic -----------------
st.sidebar.header("🎛️ Filtros Stochastic")

st.sidebar.subheader("📈 Filtro Geral - Todos Acima")
enable_above = st.sidebar.checkbox("Ativar filtro 'Todos acima'", key="enable_above")
if enable_above:
    value_above = st.sidebar.slider("Valor mínimo para os selecionados", 0, 100, 70, key="all_above")
else:
    value_above = None

st.sidebar.subheader("📉 Filtro Geral - Todos Abaixo")
enable_below = st.sidebar.checkbox("Ativar filtro 'Todos abaixo'", key="enable_below")
if enable_below:
    value_below = st.sidebar.slider("Valor máximo para os selecionados", 0, 100, 30, key="all_below")
else:
    value_below = None

st.sidebar.divider()

# ----------------- Filtro para escolher timeframe do sort MACD zero lag -----------------
macd_timeframes = [
    tf for tf in ["15m", "1h", "4h", "1d"]
    if all([
        f"{tf}_macd_zero_lag_hist" in df_valid.columns,
        f"{tf}_macd_zero_lag_hist_min" in df_valid.columns,
        f"{tf}_macd_zero_lag_hist_max" in df_valid.columns,
        f"{tf}_Close" in df_valid.columns
    ])
]

default_sort_tf = "4h" if "4h" in macd_timeframes else (macd_timeframes[0] if macd_timeframes else None)
sort_tf = st.sidebar.selectbox(
    "Timeframe para ordenação MACD 0 lag normalizado:",
    options=macd_timeframes,
    index=macd_timeframes.index(default_sort_tf) if default_sort_tf else 0
) if macd_timeframes else None

# ----------------- Aplicar Filtros Stochastic -----------------
df_filtered = df_valid.copy()

selected_stoch_columns = []
for tf in selected_timeframes:
    selected_stoch_columns += [col for col in df_valid.columns if col.startswith(f"{tf} Stoch")]

if enable_above and value_above is not None and selected_stoch_columns:
    for col in selected_stoch_columns:
        df_filtered = df_filtered[df_filtered[col] >= value_above]
    st.sidebar.success(f"Filtro ativo: Todos os selecionados ≥ {value_above}")

if enable_below and value_below is not None and selected_stoch_columns:
    for col in selected_stoch_columns:
        df_filtered = df_filtered[df_filtered[col] <= value_below]
    st.sidebar.success(f"Filtro ativo: Todos os selecionados ≤ {value_below}")

# ----------------- Ordenação e coluna final MACD zero lag normalizado (usando min/max do histograma de cada par) -----------------
if sort_tf:
    hist_col = f"{sort_tf}_macd_zero_lag_hist"
    min_col = f"{sort_tf}_macd_zero_lag_hist_min"
    max_col = f"{sort_tf}_macd_zero_lag_hist_max"
    norm_col = f"MACD0lag_norm_{sort_tf}"

    # Normaliza cada par usando seu próprio min/max histórico
    range_hist = df_filtered[max_col] - df_filtered[min_col]
    range_hist = range_hist.replace(0, 1e-9)
    df_filtered[norm_col] = (df_filtered[hist_col] - df_filtered[min_col]) / range_hist

    # Posição do zero no range
    zero_pos = (-df_filtered[min_col]) / range_hist
    df_filtered[norm_col] = 100 * (df_filtered[norm_col] - zero_pos + 0.5)
    df_filtered[norm_col] = df_filtered[norm_col].clip(0, 100)

    # Ordena pelo valor ASCENDENTE (do menor para o maior)
    df_filtered = df_filtered.sort_values(by=norm_col, ascending=True).reset_index(drop=True)
    st.sidebar.info(f"Ordenação: MACD zero lag normalizado ({sort_tf}) em ordem crescente (0→100)")

# ----------------- Exibir Resultados -----------------
if df_filtered.empty:
    st.warning("⚠️ Nenhum par atende aos filtros.")
    if not df_valid.empty:
        # Também ordena os não filtrados
        if sort_tf:
            hist_col = f"{sort_tf}_macd_zero_lag_hist"
            min_col = f"{sort_tf}_macd_zero_lag_hist_min"
            max_col = f"{sort_tf}_macd_zero_lag_hist_max"
            norm_col = f"MACD0lag_norm_{sort_tf}"
            range_hist = df_valid[max_col] - df_valid[min_col]
            range_hist = range_hist.replace(0, 1e-9)
            df_valid[norm_col] = (df_valid[hist_col] - df_valid[min_col]) / range_hist
            zero_pos = (-df_valid[min_col]) / range_hist
            df_valid[norm_col] = 100 * (df_valid[norm_col] - zero_pos + 0.5)
            df_valid[norm_col] = df_valid[norm_col].clip(0, 100)
            df_valid = df_valid.sort_values(by=norm_col, ascending=True).reset_index(drop=True)
            main_cols = ["Symbol"] + [col for col in df_valid.columns if "Stoch" in col]
            col_order = [c for c in main_cols if c in df_valid.columns] + [norm_col]
            st.write("Dados disponíveis (sem filtros, ordenados):")
            st.dataframe(df_valid[col_order], use_container_width=True)
        else:
            st.write("Dados disponíveis (sem filtros):")
            st.dataframe(df_valid, use_container_width=True)
else:
    if sort_tf:
        norm_col = f"MACD0lag_norm_{sort_tf}"
        main_cols = ["Symbol"] + [col for col in df_filtered.columns if "Stoch" in col]
        col_order = [c for c in main_cols if c in df_filtered.columns] + [norm_col]
        st.subheader(f"✅ Pares Filtrados ({len(df_filtered)} pares)")
        st.dataframe(df_filtered[col_order], use_container_width=True)
    else:
        st.subheader(f"✅ Pares Filtrados ({len(df_filtered)} pares)")
        st.dataframe(df_filtered, use_container_width=True)

if not df_valid.empty:
    st.sidebar.markdown("---")
    st.sidebar.markdown("📊 **Estatísticas**")
    st.sidebar.write(f"Total de pares: {len(df_valid)}")
    st.sidebar.write(f"Pares filtrados: {len(df_filtered)}")
    st.sidebar.write(f"Pares removidos: {len(df_valid) - len(df_filtered)}")

if failed:
    st.subheader("❌ Erros ao carregar")
    for s in failed:
        st.write(f"- {s}")
