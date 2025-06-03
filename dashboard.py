import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
st_autorefresh(interval=5000, key="filecheck")

st.title("📊 Dashboard Crypto Filtering")
st.markdown("Dev by aishend - Stochastic Version 5-3-3 & 14-3-3 ☕️")

def load_data_from_file():
    for _ in range(3):
        try:
            if os.path.exists('data_control/crypto_data.json'):
                with open('data_control/crypto_data.json', 'r') as f:
                    data = json.load(f)
                df_valid = pd.DataFrame(data.get('df_valid', []))
                failed = data.get('failed', [])
                last_update = datetime.fromisoformat(data.get('last_update', datetime.now().isoformat()))
                total_pairs = data.get('total_pairs', len(df_valid))
                # Só atualiza se o novo DataFrame for maior ou igual ao anterior
                last_len = st.session_state.get('last_len', 0)
                if len(df_valid) >= last_len:
                    st.session_state['last_df_valid'] = df_valid
                    st.session_state['last_failed'] = failed
                    st.session_state['last_last_update'] = last_update
                    st.session_state['last_total_pairs'] = total_pairs
                    st.session_state['last_file_exists'] = True
                    st.session_state['last_len'] = len(df_valid)
                # Retorna sempre o último DataFrame completo
                return (
                    st.session_state.get('last_df_valid', pd.DataFrame()),
                    st.session_state.get('last_failed', []),
                    st.session_state.get('last_last_update', datetime.now()),
                    st.session_state.get('last_total_pairs', 0),
                    st.session_state.get('last_file_exists', False)
                )
            else:
                return pd.DataFrame(), [], datetime.now(), 0, False
        except Exception:
            time.sleep(0.2)
    # Se não conseguiu ler, retorna os últimos dados válidos
    return (
        st.session_state.get('last_df_valid', pd.DataFrame()),
        st.session_state.get('last_failed', []),
        st.session_state.get('last_last_update', datetime.now()),
        st.session_state.get('last_total_pairs', 0),
        st.session_state.get('last_file_exists', False)
    )

df_valid, failed, last_update_time, total_pairs, file_exists = load_data_from_file()

# ----------- Sidebar: Barra de Progresso e Status ----------- #
with st.sidebar:
    if file_exists:
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

    st.subheader("🎯 Filtro Extremos (abaixo/acima)")
    enable_extremos = st.checkbox("Ativar filtro de extremos", key="enable_extremos")
    extremos_min, extremos_max = st.slider(
        "Defina os valores dos extremos (mínimo e máximo)",
        0, 100, (30, 70), key="extremos_range"
    )

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

if enable_extremos and selected_stoch_columns:
    mask_extremos = df_filtered[selected_stoch_columns].apply(
        lambda row: all((v <= extremos_min or v >= extremos_max) for v in row), axis=1
    )
    df_filtered = df_filtered[mask_extremos]
    st.sidebar.success(f"Filtro ativo: Todos os selecionados ≤ {extremos_min} ou ≥ {extremos_max} (extremos)")

# ----------- Ordenação: mais próximo de 50 no topo ----------- #
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

    # Ordenação: mais próximo de 50 no topo
    df_filtered = df_filtered.loc[(df_filtered[norm_col] - 50).abs().sort_values().index].reset_index(drop=True)
    st.sidebar.info(f"Ordenação: MACD normalizado mais próximo de 50 (cruzamento) no topo")

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
            # Ordenação: mais próximo de 50 no topo
            df_valid = df_valid.loc[(df_valid[norm_col] - 50).abs().sort_values().index].reset_index(drop=True)
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
