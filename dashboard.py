import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")

# Auto-refresh a cada 5 minutos para verificar arquivo
count = st_autorefresh(interval=300000, key="filecheck")

st.title("Varredura Interativa de Pares – Stochastic (15m, 1h & 4h)")
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

# ----------------- Filtros Gerais -----------------
st.sidebar.header("🎛️ Filtros Stochastic")

st.sidebar.subheader("📈 Filtro Geral - Todos Acima")
enable_above = st.sidebar.checkbox("Ativar filtro 'Todos acima'", key="enable_above")
if enable_above:
    value_above = st.sidebar.slider("Valor mínimo para TODOS os Stochs", 0, 100, 70, key="all_above")
else:
    value_above = None

st.sidebar.subheader("📉 Filtro Geral - Todos Abaixo")
enable_below = st.sidebar.checkbox("Ativar filtro 'Todos abaixo'", key="enable_below")
if enable_below:
    value_below = st.sidebar.slider("Valor máximo para TODOS os Stochs", 0, 100, 30, key="all_below")
else:
    value_below = None

st.sidebar.divider()

# ----------------- Filtros Especiais -----------------
st.sidebar.header("Filtros Especiais Rápidos")
col1, col2 = st.sidebar.columns(2)
with col1:
    ativar_4h_acima = st.button("4h acima + 3 acima")
with col2:
    ativar_4h_abaixo = st.button("4h abaixo + 3 abaixo")

# ----------------- Aplicar Filtros -----------------
df_filtered = df_valid.copy()
stoch_columns = [col for col in df_valid.columns if 'Stoch' in col]
stoch_4h_columns = [col for col in stoch_columns if col.startswith('4h')]
other_stoch_columns = [col for col in stoch_columns if not col.startswith('4h')]

# Filtro "Todos acima"
if enable_above and value_above is not None:
    for col in stoch_columns:
        df_filtered = df_filtered[df_filtered[col] >= value_above]
    st.sidebar.success(f"Filtro ativo: Todos ≥ {value_above}")

# Filtro "Todos abaixo"
if enable_below and value_below is not None:
    for col in stoch_columns:
        df_filtered = df_filtered[df_filtered[col] <= value_below]
    st.sidebar.success(f"Filtro ativo: Todos ≤ {value_below}")

# Filtro especial: 4h acima + 3 acima
if ativar_4h_acima:
    value_4h = st.sidebar.number_input("Valor mínimo para 4h (acima)", 0, 100, 70, key="4h_acima")
    value_3 = st.sidebar.number_input("Valor mínimo para 3 outros (acima)", 0, 100, 70, key="3_acima")
    mask_4h = df_filtered[stoch_4h_columns].ge(value_4h).all(axis=1)
    mask_others = df_filtered[other_stoch_columns].ge(value_3).sum(axis=1) >= 3
    df_filtered = df_filtered[mask_4h & mask_others]
    st.sidebar.success(f"Filtro especial: 4h ≥ {value_4h} e pelo menos 3 outros ≥ {value_3}")

# Filtro especial: 4h abaixo + 3 abaixo
if ativar_4h_abaixo:
    value_4h = st.sidebar.number_input("Valor máximo para 4h (abaixo)", 0, 100, 30, key="4h_abaixo")
    value_3 = st.sidebar.number_input("Valor máximo para 3 outros (abaixo)", 0, 100, 30, key="3_abaixo")
    mask_4h = df_filtered[stoch_4h_columns].le(value_4h).all(axis=1)
    mask_others = df_filtered[other_stoch_columns].le(value_3).sum(axis=1) >= 3
    df_filtered = df_filtered[mask_4h & mask_others]
    st.sidebar.success(f"Filtro especial: 4h ≤ {value_4h} e pelo menos 3 outros ≤ {value_3}")

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
