import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")

# Auto-refresh a cada 5 minutos para verificar arquivo
count = st_autorefresh(interval=300000, key="filecheck")

st.title("Varredura Interativa de Pares – Stochastic (15m, 1h, 4h & 1d)")
st.markdown("Dev by aishend feat chatgpt — versão Stochastic 5-3-3 & 14-3-3 ☕️")

@st.cache_data(ttl=60)
def load_data_from_file():
    try:
        if os.path.exists('crypto_data.json'):
            with open('crypto_data.json', 'r') as f:
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

# Carregar dados
df_valid, failed, last_update_time, file_exists = load_data_from_file()

# Sidebar
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

# ----------------- Seleção de Timeframes -----------------
st.sidebar.header("Timeframes para Filtro")
# Lista possível de timeframes (ajuste conforme os nomes das colunas do seu DataFrame)
all_timeframes = []
for tf in ["15m", "1h", "4h", "1d"]:
    if any(col.startswith(f"{tf} Stoch") for col in df_valid.columns):
        all_timeframes.append(tf)

default_timeframes = [tf for tf in ["1h", "4h", "1d"] if tf in all_timeframes]
selected_timeframes = st.sidebar.multiselect(
    "Selecione os timeframes para aplicar os filtros:",
    options=all_timeframes,
    default=default_timeframes
)

# ----------------- Filtros Gerais -----------------
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

# ----------------- Aplicar Filtros -----------------
df_filtered = df_valid.copy()

# Pega as colunas dos timeframes selecionados
selected_stoch_columns = []
for tf in selected_timeframes:
    selected_stoch_columns += [col for col in df_valid.columns if col.startswith(f"{tf} Stoch")]

# Filtro "Todos acima"
if enable_above and value_above is not None and selected_stoch_columns:
    for col in selected_stoch_columns:
        df_filtered = df_filtered[df_filtered[col] >= value_above]
    st.sidebar.success(f"Filtro ativo: Todos os selecionados ≥ {value_above}")

# Filtro "Todos abaixo"
if enable_below and value_below is not None and selected_stoch_columns:
    for col in selected_stoch_columns:
        df_filtered = df_filtered[df_filtered[col] <= value_below]
    st.sidebar.success(f"Filtro ativo: Todos os selecionados ≤ {value_below}")

# ----------------- Ordenação pelo MACD zero lag -----------------
# Ordena pelo MACD zero lag do timeframe selecionado mais "alto" (prioridade: 1d > 4h > 1h > 15m)
macd_col = None
for tf in ["1d", "4h", "1h", "15m"]:
    if tf in selected_timeframes:
        col_name = f"{tf}_macd_zero_lag_hist"
        if col_name in df_filtered.columns:
            macd_col = col_name
            break
if macd_col:
    df_filtered = df_filtered.loc[df_filtered[macd_col].abs().sort_values().index].reset_index(drop=True)

# ----------------- Exibir Resultados -----------------
if df_filtered.empty:
    st.warning("⚠️ Nenhum par atende aos filtros.")
    if not df_valid.empty:
        st.write("Dados disponíveis (sem filtros):")
        st.dataframe(df_valid, use_container_width=True)
else:
    st.subheader(f"✅ Pares Filtrados ({len(df_filtered)} pares)")
    st.table(df_filtered)

# Estatísticas
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
