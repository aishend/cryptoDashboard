# update_trading_pairs.py

import sys
import os
import importlib.util
try:
    from binance_client.binance_client import get_futures_pairs
except ImportError:
    # fallback para execução direta
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from binance_client.binance_client import get_futures_pairs

def write_pairs_to_file(pairs, filename="trading_pairs.py"):
    with open(filename, "w") as f:
        f.write("# Arquivo gerado automaticamente\n")
        f.write("TRADING_PAIRS = [\n")
        for p in pairs:
            f.write(f"    '{p}',\n")
        f.write("]\n")

if __name__ == "__main__":
    try:
        pairs = get_futures_pairs()
        write_pairs_to_file(pairs)
        print(f"[OK] Arquivo trading_pairs.py atualizado com {len(pairs)} pares de futuros perpétuos.")
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar trading_pairs22.py: {e}")
        sys.exit(1)

