import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
# Atualiza a cada 5 segundos para mostrar progresso em tempo real
st_autorefresh(interval=5000, key="filecheck")

st.title("📊 Dashboard Crypto Filtering")
st.markdown("Dev by aishend - Stochastic Version 5-3-3 & 14-3-3 ☕️")

@st.cache_data(ttl=2)
def load_data_from_file():
    try:
        if os.path.exists('data_control/crypto_data.json'):
            with open('data_control/crypto_data.json', 'r') as f:
                data = json.load(f)
            df_valid = pd.DataFrame(data['df_valid'])
            failed = data.get('failed', [])
            last_update = datetime.fromisoformat(data.get('last_update', datetime.now().isoformat()))
            total_pairs = data.get('total_pairs', len(df_valid))
            return df_valid, failed, last_update, total_pairs, True
        else:
            return pd.DataFrame(), [], datetime.now(), 0, False
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), [], datetime.now(), 0, False

df_valid, failed, last_update_time, total_pairs, file_exists = load_data_from_file()

# ----------- Sidebar: Barra de Progresso e Status ----------- #
with st.sidebar:
    if file_exists:
        st.success(f"✅ Dados carregados: {last_update_time.strftime('%H:%M:%S')}")
        time_diff = datetime.now() - last_update_time
        minutes_ago = int(time_diff.total_seconds() / 60)
        st.info(f"📅 Atualizado há {minutes_ago} minutos")
    else:
        st.error("❌ Arquivo de dados não encontrado")

    # PROGRESSO DINÂMICO
    ready = len(df_valid)
    if total_pairs:
        progress = ready / total_pairs
        st.progress(progress, text=f"Pares processados: {ready}/{total_pairs}")
        st.caption(f"Pares processados: {ready}/{total_pairs}")
    else:
        st.caption(f"Pares processados: {ready}")

    # Botão de atualização
    if st.button("🔄 Recarregar Dados"):
        load_data_from_file.clear()
        st.rerun()

    st.markdown("---")

    st.header("Timeframes para Filtro")
    all_timeframes = []
    for tf in ["15m", "1h", "4h", "1d"]:
        if any(col.startswith(f"{tf} Stoch") for col in df_valid.columns):
            all_timeframes.append(tf)
    default_timeframes = [tf for tf in ["1h", "4h"] if tf in all_timeframes]
    selected_timeframes = st.multiselect(
        "Selecione os timeframes para aplicar os filtros:",
        options=all_timeframes,
        default=default_timeframes
    )

    st.header("🎛️ Filtros Stochastic")
    st.subheader("📈 Filtro Geral - Todos Acima")
    enable_above = st.checkbox("Ativar filtro 'Todos acima'", key="enable_above")
    if enable_above:
        value_above = st.slider("Valor mínimo para os selecionados", 0, 100, 70, key="all_above")
    else:
        value_above = None

    st.subheader("📉 Filtro Geral - Todos Abaixo")
    enable_below = st.checkbox("Ativar filtro 'Todos abaixo'", key="enable_below")
    if enable_below:
        value_below = st.slider("Valor máximo para os selecionados", 0, 100, 30, key="all_below")
    else:
        value_below = None

    st.divider()

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
    sort_tf = st.selectbox(
        "Timeframe para ordenação MACD 0 lag normalizado:",
        options=macd_timeframes,
        index=macd_timeframes.index(default_sort_tf) if default_sort_tf else 0
    ) if macd_timeframes else None

# ----------- Aplicar Filtros Stochastic ----------- #
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

# ----------- Ordenação e coluna final MACD zero lag normalizado ----------- #
if sort_tf:
    hist_col = f"{sort_tf}_macd_zero_lag_hist"
    min_col = f"{sort_tf}_macd_zero_lag_hist_min"
    max_col = f"{sort_tf}_macd_zero_lag_hist_max"
    norm_col = f"MACD0lag_norm_{sort_tf}"

    range_hist = df_filtered[max_col] - df_filtered[min_col]
    range_hist = range_hist.replace(0, 1e-9)
    df_filtered[norm_col] = (df_filtered[hist_col] - df_filtered[min_col]) / range_hist
    zero_pos = (-df_filtered[min_col]) / range_hist
    df_filtered[norm_col] = 100 * (df_filtered[norm_col] - zero_pos + 0.5)
    df_filtered[norm_col] = df_filtered[norm_col].clip(0, 100)
    df_filtered = df_filtered.sort_values(by=norm_col, ascending=True).reset_index(drop=True)
    st.sidebar.info(f"Ordenação: MACD zero lag normalizado ({sort_tf}) em ordem crescente (0→100)")

# ----------- Exibir Resultados ----------- #
if df_filtered.empty:
    st.warning("⚠️ Nenhum par atende aos filtros.")
    if not df_valid.empty:
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
