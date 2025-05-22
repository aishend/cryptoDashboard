import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")

# Auto-refresh a cada 5 minutos para verificar arquivo
count = st_autorefresh(interval=300000, key="filecheck")

st.title("Varredura Interativa de Pares – Apenas Stochastic (1h & 4h)")
st.markdown("Dev by aishend feat chatgpt — versão só Stochastic 5-3-3 & 14-3-3 ☕️")


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

    # Calcular tempo desde última atualização
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
# Filtros (mantém igual)
# ------------------------------------------------------------
st.sidebar.header("Filtros Stochastic")
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

# Aplicar filtros
df_filtered = df_valid.copy()

for column, (mode, low, up) in filters.items():
    if mode == "Inferior" and low is not None:
        df_filtered = df_filtered[df_filtered[column] < low]
    elif mode == "Superior" and up is not None:
        df_filtered = df_filtered[df_filtered[column] > up]
    elif mode == "Ambos" and low is not None and up is not None:
        df_filtered = df_filtered[(df_filtered[column] < low) | (df_filtered[column] > up)]

# Exibir resultados
if df_filtered.empty:
    st.warning("⚠️ Nenhum par atende aos filtros.")
    if not df_valid.empty:
        st.write("Dados disponíveis (sem filtros):")
        st.dataframe(df_valid, use_container_width=True)
else:
    st.subheader("✅ Pares Filtrados")
    st.table(df_filtered)

if failed:
    st.subheader("❌ Erros ao carregar")
    for s in failed:
        st.write(f"- {s}")
