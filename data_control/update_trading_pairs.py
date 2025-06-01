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
    # Garante que o diretório existe antes de escrever o arquivo
    dir_path = os.path.dirname(os.path.abspath(filename))
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
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
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar trading_pairs.py: {e}")
        sys.exit(1)
