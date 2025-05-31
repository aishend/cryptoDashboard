# update_trading_pairs.py

import os
import sys
import importlib.util

# 1. Carrega as credenciais da Binance
try:
    from binance_client.config import KEY, SECRET
except ImportError:
    try:
        from config import KEY, SECRET
    except ImportError:
        config_path = os.path.join(os.path.dirname(__file__), 'config.py')
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                f.write('KEY = "COLOQUE_SUA_BINANCE_API_KEY_AQUI"\n')
                f.write('SECRET = "COLOQUE_SUA_BINANCE_API_SECRET_AQUI"\n')
            print(f"Arquivo config.py criado em {config_path}. Coloque sua KEY e SECRET nele.")
            sys.exit(1)
        spec = importlib.util.spec_from_file_location("config", config_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        KEY = config.KEY
        SECRET = config.SECRET

from binance.client import Client

def get_futures_pairs():
    client = Client(KEY, SECRET)
    info = client.futures_exchange_info()
    # Pega apenas símbolos de contratos perpétuos ativos
    pairs = [
        s['symbol']
        for s in info['symbols']
        if s['status'] == 'TRADING' and s['contractType'] == 'PERPETUAL'
    ]
    return sorted(pairs)

def write_pairs_to_file(pairs, filename="trading_pairs22.py"):
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
        # Substitua o emoji ✅ por texto
        print(f"[OK] Arquivo trading_pairs22.py atualizado com {len(pairs)} pares de futuros perpétuos.")
    except Exception as e:
        # Substitua o emoji ❌ por texto
        print(f"[ERRO] Erro ao atualizar trading_pairs22.py: {e}")
        sys.exit(1)