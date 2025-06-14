import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import pandas_ta as ta
import json
import logging
from datetime import datetime
from pathlib import Path

try:
    from data_control.analysis import analyze_timeframe
except ImportError:
    from analysis import analyze_timeframe

try:
    from trading_pairs.trading_pairs import TRADING_PAIRS
except ImportError:
    from trading_pairs import TRADING_PAIRS

from indicators_set.indicators import calc_macd_zero_lag

logging.basicConfig(level=logging.INFO)

def _calc_stoch(df: pd.DataFrame, k: int, d: int, smooth_k: int, label_prefix: str):
    if not all(col in df.columns for col in ["High", "Low", "Close"]):
        raise KeyError(f"DataFrame sem colunas necessárias, colunas: {df.columns.tolist()}")
    stoch = ta.stoch(df["High"], df["Low"], df["Close"], k=k, d=d, smooth_k=smooth_k)
    df[f"{label_prefix}_stoch_{k}"] = stoch.iloc[:, 0]
    return df

def safe_json_write(data, final_path):
    temp_path = str(final_path) + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, final_path)

def scan_pairs():
    valid_rows = []
    failed_pairs = []
    total_pairs = len(TRADING_PAIRS)
    json_path = Path(__file__).parent / "crypto_data.json"

    for idx, symbol in enumerate(TRADING_PAIRS):
        try:
            df_15m = analyze_timeframe(symbol, "15m", "1 day ago UTC")
            df_1h = analyze_timeframe(symbol, "1h", "7 day ago UTC")
            df_4h = analyze_timeframe(symbol, "4h", "30 day ago UTC")
            df_1d = analyze_timeframe(symbol, "1d", "180 day ago UTC")

            if df_1h.empty or df_4h.empty or df_1d.empty:
                failed_pairs.append(symbol)
                continue

            result_data = {"Symbol": symbol}

            # 15m
            if not df_15m.empty:
                _calc_stoch(df_15m, 5, 3, 3, "15m_5")
                _calc_stoch(df_15m, 14, 3, 3, "15m_14")
                last_15m = df_15m.iloc[-1]
                macd_line, signal_line, macd_hist = calc_macd_zero_lag(df_15m['Close'])
                result_data.update({
                    "15m Stoch 5-3-3": round(last_15m["15m_5_stoch_5"], 2),
                    "15m Stoch 14-3-3": round(last_15m["15m_14_stoch_14"], 2),
                    "15m_macd_zero_lag_hist": round(macd_hist.iloc[-1], 6),
                    "15m_macd_zero_lag_hist_min": round(macd_hist.min(), 6),
                    "15m_macd_zero_lag_hist_max": round(macd_hist.max(), 6),
                    "15m_Close": round(last_15m["Close"], 6)
                })

            # 1h, 4h, 1d
            for df, tf in ((df_1h, "1h"), (df_4h, "4h"), (df_1d, "1d")):
                _calc_stoch(df, 5, 3, 3, f"{tf}_5")
                _calc_stoch(df, 14, 3, 3, f"{tf}_14")
                last_row = df.iloc[-1]
                macd_line, signal_line, macd_hist = calc_macd_zero_lag(df['Close'])
                result_data.update({
                    f"{tf} Stoch 5-3-3": round(last_row[f"{tf}_5_stoch_5"], 2),
                    f"{tf} Stoch 14-3-3": round(last_row[f"{tf}_14_stoch_14"], 2),
                    f"{tf}_macd_zero_lag_hist": round(macd_hist.iloc[-1], 6),
                    f"{tf}_macd_zero_lag_hist_min": round(macd_hist.min(), 6),
                    f"{tf}_macd_zero_lag_hist_max": round(macd_hist.max(), 6),
                    f"{tf}_Close": round(last_row["Close"], 6)
                })

            valid_rows.append(result_data)
        except Exception as exc:
            logging.warning(f"Falha ao processar {symbol}: {exc}")
            failed_pairs.append(symbol)

        # Salva incrementalmente a cada par processado, de forma atômica
        data = {
            'df_valid': valid_rows,
            'failed': failed_pairs,
            'last_update': datetime.now().isoformat(),
            'total_pairs': len(TRADING_PAIRS)
        }
        safe_json_write(data, json_path)

    return pd.DataFrame(valid_rows), failed_pairs

def update_data():
    try:
        scan_pairs()
    except Exception as e:
        print(f"[ERRO] Erro na atualização: {e}")

if __name__ == "__main__":
    update_data()
