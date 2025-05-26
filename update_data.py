import pandas as pd
import pandas_ta as ta
import json
import logging
from datetime import datetime
from analysis import analyze_timeframe
# from trading_pairs import TRADING_PAIRS
from trading_pairs22 import TRADING_PAIRS
from pathlib import Path

logging.basicConfig(level=logging.INFO)

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
            # Usar '15m', '1h', '4h' conforme documentação oficial da Binance[1]
            df_15m = analyze_timeframe(symbol, "15m", "1 day ago UTC")
            df_1h = analyze_timeframe(symbol, "1h", "7 day ago UTC")
            df_4h = analyze_timeframe(symbol, "4h", "30 day ago UTC")
            # Se algum dos principais timeframes estiver vazio, pula o par
            if df_1h.empty or df_4h.empty:
                failed_pairs.append(symbol)
                continue
            result_data = {"Symbol": symbol}
            # 15m só adiciona se não estiver vazio
            if not df_15m.empty:
                _calc_stoch(df_15m, 5, 3, 3, "15m_5")
                _calc_stoch(df_15m, 14, 3, 3, "15m_14")
                last_15m = df_15m.iloc[-1]
                result_data.update({
                    "15m Stoch 5-3-3": round(last_15m["15m_5_stoch_5"], 2),
                    "15m Stoch 14-3-3": round(last_15m["15m_14_stoch_14"], 2),
                })
            for df, tf in ((df_1h, "1h"), (df_4h, "4h")):
                _calc_stoch(df, 5, 3, 3, f"{tf}_5")
                _calc_stoch(df, 14, 3, 3, f"{tf}_14")
            last_1h = df_1h.iloc[-1]
            last_4h = df_4h.iloc[-1]
            result_data.update({
                "1h Stoch 5-3-3": round(last_1h["1h_5_stoch_5"], 2),
                "1h Stoch 14-3-3": round(last_1h["1h_14_stoch_14"], 2),
                "4h Stoch 5-3-3": round(last_4h["4h_5_stoch_5"], 2),
                "4h Stoch 14-3-3": round(last_4h["4h_14_stoch_14"], 2),
            })
            valid_rows.append(result_data)
        except Exception as exc:
            logging.warning(f"Falha ao processar {symbol}: {exc}")
            failed_pairs.append(symbol)
    return pd.DataFrame(valid_rows), failed_pairs

def update_data():
    print(f"🔄 Atualizando dados: {datetime.now()}")
    try:
        df_valid, failed = scan_pairs()
        # Caminho seguro para o arquivo JSON no mesmo diretório do script
        json_path = Path(__file__).parent / "crypto_data.json"
        data = {
            'df_valid': df_valid.to_dict('records') if not df_valid.empty else [],
            'failed': failed,
            'last_update': datetime.now().isoformat(),
            'total_pairs': len(df_valid)
        }
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Dados salvos: {len(df_valid)} pares válidos, {len(failed)} com erro")
        if not df_valid.empty:
            print(f"📊 Colunas disponíveis: {list(df_valid.columns)}")
    except Exception as e:
        print(f"❌ Erro na atualização: {e}")

if __name__ == "__main__":
    update_data()
