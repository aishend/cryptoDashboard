import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import numpy as np
import sys
import subprocess

st.set_page_config(layout="wide", page_icon="📈", page_title="Crypto Dashboard")

# Configurar autorefresh a cada 1 minuto
refresh_interval = st_autorefresh(interval=60 * 1000, key="dashboard_refresh")


def safe_run_update(script_path):
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            st.info(f"Atualização: {result.stdout}")
    except subprocess.CalledProcessError as e:
        st.error(f"Erro na atualização:\n{'-' * 30}\n"
                 f"Saída: {e.stdout}\n"
                 f"Erro: {e.stderr}\n"
                 f"{'-' * 30}")
        st.stop()


# Executar atualizações
with st.spinner("Verificando atualizações..."):
    safe_run_update("trading_pairs/update_trading_pairs.py")
    safe_run_update("data_control/update_data.py")


@st.cache_data(ttl=30, show_spinner="Carregando dados...")
def load_data_from_file():
    try:
        if os.path.exists('data_control/crypto_data.json'):
            with open('data_control/crypto_data.json', 'r') as f:
                data = json.load(f)

            df_valid = pd.DataFrame(data['df_valid'])
            failed = data['failed']
            last_update = datetime.fromisoformat(data['last_update'])

            # Converter tipos numéricos
            numeric_cols = [col for col in df_valid.columns if col not in ['Symbol']]
            df_valid[numeric_cols] = df_valid[numeric_cols].apply(pd.to_numeric, errors='coerce')

            return df_valid, failed, last_update, True
        return pd.DataFrame(), [], datetime.now(), False
    except Exception as e:
        st.error(f"Erro crítico ao carregar dados: {e}")
        return pd.DataFrame(), [], datetime.now(), False


# Interface principal
st.title("📊 Dashboard Crypto Filtering")
st.markdown("**Dev by aishend** - Stochastic 5-3-3 & 14-3-3 | MACD Zero Lag")

# Carregar dados
df_valid, failed, last_update_time, file_exists = load_data_from_file()

# Sidebar - Status
st.sidebar.header("Status do Sistema")
if file_exists:
    st.sidebar.success(f"✅ Dados carregados: {last_update_time.strftime('%d/%m %H:%M:%S')}")
    time_diff = datetime.now() - last_update_time
    minutes_ago = int(time_diff.total_seconds() / 60)
    st.sidebar.progress(min(minutes_ago / 5, 1.0))
    st.sidebar.caption(f"Atualizado há {minutes_ago} minutos")
else:
    st.sidebar.error("❌ Arquivo de dados não encontrado")

# Controles de atualização
if st.sidebar.button("🔄 Forçar Atualização Completa"):
    load_data_from_file.clear()
    st.rerun()

# Filtros
st.sidebar.header("Filtros")

# Seleção de Timeframes
all_timeframes = [tf for tf in ["15m", "1h", "4h", "1d"]
                  if any(col.startswith(f"{tf} Stoch") for col in df_valid.columns)]
selected_timeframes = st.sidebar.multiselect(
    "Timeframes para Filtro:",
    options=all_timeframes,
    default=["1h", "4h"]
)

# Filtros Stochastic
st.sidebar.subheader("Filtros Stochastic")
col1, col2 = st.sidebar.columns(2)
with col1:
    enable_above = st.checkbox("Todos Acima", key="above")
    value_above = st.slider("Valor Mínimo", 0, 100, 70) if enable_above else None
with col2:
    enable_below = st.checkbox("Todos Abaixo", key="below")
    value_below = st.slider("Valor Máximo", 0, 100, 30) if enable_below else None

# Filtro MACD
macd_timeframes = [
    tf for tf in ["15m", "1h", "4h", "1d"]
    if all(f"{tf}_macd_zero_lag_hist{sfx}" in df_valid.columns
           for sfx in ['', '_min', '_max']) and f"{tf}_Close" in df_valid.columns
]

if macd_timeframes:
    st.sidebar.divider()
    sort_tf = st.sidebar.selectbox(
        "Ordenação MACD:",
        options=macd_timeframes,
        index=macd_timeframes.index("4h") if "4h" in macd_timeframes else 0,
        format_func=lambda x: f"{x.upper()} Normalizado"
    )

    # Normalização MACD
    hist_col = f"{sort_tf}_macd_zero_lag_hist"
    min_col = f"{sort_tf}_macd_zero_lag_hist_min"
    max_col = f"{sort_tf}_macd_zero_lag_hist_max"

    if not df_valid.empty:
        df_valid[f"MACD_norm_{sort_tf}"] = df_valid.apply(
            lambda row: 100 * (row[hist_col] - row[min_col]) /
                        (row[max_col] - row[min_col] + 1e-9),
            axis=1
        )
        df_valid = df_valid.sort_values(by=f"MACD_norm_{sort_tf}", ascending=True)

# Aplicar Filtros
df_filtered = df_valid.copy()
if selected_timeframes:
    for tf in selected_timeframes:
        cols = [c for c in df_valid.columns if c.startswith(f"{tf} Stoch")]
        if enable_above and value_above:
            for col in cols:
                df_filtered = df_filtered[df_filtered[col] >= value_above]
        if enable_below and value_below:
            for col in cols:
                df_filtered = df_filtered[df_filtered[col] <= value_below]

# Exibição de Resultados
tab1, tab2 = st.tabs(["📈 Pares Filtrados", "📊 Estatísticas"])

with tab1:
    if not df_filtered.empty:
        cols_to_show = ["Symbol"] + [c for c in df_filtered.columns if "Stoch" in c]
        if macd_timeframes:
            cols_to_show += [f"MACD_norm_{sort_tf}"]

        st.dataframe(
            df_filtered[cols_to_show].sort_values(by=f"MACD_norm_{sort_tf}", ascending=True),
            use_container_width=True,
            height=600
        )
    else:
        st.warning("Nenhum par corresponde aos filtros atuais")
        st.write("Dados completos disponíveis:")
        st.dataframe(df_valid, use_container_width=True)

with tab2:
    if not df_valid.empty:
        st.metric("Total de Pares", len(df_valid))
        st.metric("Pares Filtrados", len(df_filtered))
        st.metric("Taxa de Sucesso", f"{(len(df_filtered) / len(df_valid) * 100):.1f}%")

        if macd_timeframes:
            st.divider()
            st.line_chart(df_valid.set_index('Symbol')[f"MACD_norm_{sort_tf}"].nlargest(20))

# Exibir erros
if failed:
    st.sidebar.divider()
    with st.sidebar.expander("⚠️ Erros Detalhados"):
        for s in failed:
            st.write(f"- {s}")
