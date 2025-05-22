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

# ------------------------------------------------------------
# Carregar dados do arquivo JSON
# ------------------------------------------------------------
@st.cache_data(ttl=60)  # Cache por 1 minuto
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

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
if file_exists:
    st.sidebar.success(f"✅ Dados carregados: {last_update_time.strftime('%H:%M:%S')}")
    time_diff = datetime.now() - last_update_time
    minutes_ago = int(time_diff.total_seconds() / 60)
    st.sidebar.info(f"📅 Atualizado há {minutes_ago} minutos")
else:
    st.sidebar.error("❌ Arquivo de dados não encontrado")

# Botão para forçar reload
if st.sidebar.button("🔄 Recarregar Dados"):
    load_data_from_file.clear()
    st.rerun()

# ------------------------------------------------------------
# Filtros Simplificados
# ------------------------------------------------------------
st.sidebar.header("🎛️ Filtros Stochastic")

# Filtro geral "Todos acima"
st.sidebar.subheader("📈 Filtro Geral - Todos Acima")
enable_above = st.sidebar.checkbox("Ativar filtro 'Todos acima'", key="enable_above")
if enable_above:
    value_above = st.sidebar.slider("Valor mínimo para TODOS os Stochs", 0, 100, 70, key="all_above")
else:
    value_above = None

# Filtro geral "Todos abaixo"
st.sidebar.subheader("📉 Filtro Geral - Todos Abaixo")
enable_below = st.sidebar.checkbox("Ativar filtro 'Todos abaixo'", key="enable_below")
if enable_below:
    value_below = st.sidebar.slider("Valor máximo para TODOS os Stochs", 0, 100, 30, key="all_below")
else:
    value_below = None

st.sidebar.divider()

# Filtros específicos para 5-3-3
st.sidebar.subheader("⚡ Filtro Específico - Stoch 5-3-3")
filter_533 = st.sidebar.selectbox(
    "Filtrar Stoch 5-3-3:",
    ["Nenhum", "Acima", "Abaixo", "Entre valores"],
    key="filter_533"
)

if filter_533 == "Acima":
    value_533_above = st.sidebar.number_input("5-3-3 acima de:", 0, 100, 70, key="533_above")
elif filter_533 == "Abaixo":
    value_533_below = st.sidebar.number_input("5-3-3 abaixo de:", 0, 100, 30, key="533_below")
elif filter_533 == "Entre valores":
    value_533_min = st.sidebar.number_input("5-3-3 mínimo:", 0, 100, 30, key="533_min")
    value_533_max = st.sidebar.number_input("5-3-3 máximo:", 0, 100, 70, key="533_max")

# Filtros específicos para 14-3-3
st.sidebar.subheader("🔋 Filtro Específico - Stoch 14-3-3")
filter_1433 = st.sidebar.selectbox(
    "Filtrar Stoch 14-3-3:",
    ["Nenhum", "Acima", "Abaixo", "Entre valores"],
    key="filter_1433"
)

if filter_1433 == "Acima":
    value_1433_above = st.sidebar.number_input("14-3-3 acima de:", 0, 100, 70, key="1433_above")
elif filter_1433 == "Abaixo":
    value_1433_below = st.sidebar.number_input("14-3-3 abaixo de:", 0, 100, 30, key="1433_below")
elif filter_1433 == "Entre valores":
    value_1433_min = st.sidebar.number_input("14-3-3 mínimo:", 0, 100, 30, key="1433_min")
    value_1433_max = st.sidebar.number_input("14-3-3 máximo:", 0, 100, 70, key="1433_max")

# ------------------------------------------------------------
# Aplicar filtros
# ------------------------------------------------------------
df_filtered = df_valid.copy()

# Colunas dos stochastics (incluindo 15m se existirem)
stoch_columns = [col for col in df_valid.columns if 'Stoch' in col]
stoch_533_columns = [col for col in stoch_columns if '5-3-3' in col]
stoch_1433_columns = [col for col in stoch_columns if '14-3-3' in col]

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

# Filtro específico 5-3-3
if filter_533 == "Acima":
    for col in stoch_533_columns:
        df_filtered = df_filtered[df_filtered[col] >= value_533_above]
    st.sidebar.info(f"5-3-3 ≥ {value_533_above}")
elif filter_533 == "Abaixo":
    for col in stoch_533_columns:
        df_filtered = df_filtered[df_filtered[col] <= value_533_below]
    st.sidebar.info(f"5-3-3 ≤ {value_533_below}")
elif filter_533 == "Entre valores":
    for col in stoch_533_columns:
        df_filtered = df_filtered[(df_filtered[col] >= value_533_min) & (df_filtered[col] <= value_533_max)]
    st.sidebar.info(f"5-3-3 entre {value_533_min} e {value_533_max}")

# Filtro específico 14-3-3
if filter_1433 == "Acima":
    for col in stoch_1433_columns:
        df_filtered = df_filtered[df_filtered[col] >= value_1433_above]
    st.sidebar.info(f"14-3-3 ≥ {value_1433_above}")
elif filter_1433 == "Abaixo":
    for col in stoch_1433_columns:
        df_filtered = df_filtered[df_filtered[col] <= value_1433_below]
    st.sidebar.info(f"14-3-3 ≤ {value_1433_below}")
elif filter_1433 == "Entre valores":
    for col in stoch_1433_columns:
        df_filtered = df_filtered[(df_filtered[col] >= value_1433_min) & (df_filtered[col] <= value_1433_max)]
    st.sidebar.info(f"14-3-3 entre {value_1433_min} e {value_1433_max}")

# ------------------------------------------------------------
# Exibir resultados
# ------------------------------------------------------------
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
