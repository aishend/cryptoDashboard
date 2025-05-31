from binance.client import Client
from binance_client.config import KEY, SECRET  # Suas credenciais, NÃO coloque no git!

client = Client(KEY, SECRET)

def get_futures_pairs():
    info = client.futures_exchange_info()
    # Pega apenas símbolos de contratos perpetuates ativos (os mais comuns)
    pairs = [
        s['symbol']
        for s in info['symbols']
        if s['status'] == 'TRADING' and s['contractType'] == 'PERPETUAL'
    ]
    return sorted(pairs)

def write_pairs_to_file(pairs, filename="trading_pairs.py"):
    with open(filename, "w") as f:
        f.write("# Arquivo gerado automaticamente\n")
        f.write("TRADING_PAIRS = [\n")
        for p in pairs:
            f.write(f"    '{p}',\n")
        f.write("]\n")

if __name__ == "__main__":
    all_pairs = get_futures_pairs()
    write_pairs_to_file(all_pairs)
    print(f"Arquivo trading_pairs.py atualizado com {len(all_pairs)} pares.")
