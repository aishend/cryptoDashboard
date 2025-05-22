import concurrent.futures
import logging
from binance_client import get_futures_positions
from trading_pairs1 import TRADING_PAIRS

# Configuração básica de logging para debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def process_symbol(symbol):
    """
    Busca as posições do par e filtra somente aquelas em aberto (positionAmt != 0).
    Retorna uma tupla (symbol, DataFrame) se houver posição aberta ou None caso contrário.
    """
    logging.debug(f"Iniciando verificação para {symbol}")
    df = get_futures_positions(symbol)
    if df.empty:
        logging.debug(f"{symbol}: Sem dados de posição.")
        return None
    try:
        # Converte a coluna 'positionAmt' para float para possibilitar a comparação
        df["positionAmt"] = df["positionAmt"].astype(float)
    except Exception as e:
        logging.exception(f"{symbol}: Erro ao converter positionAmt - {e}")
        return None

    # Filtra apenas posições com quantidade diferente de zero
    df_abertas = df[df["positionAmt"] != 0]
    if not df_abertas.empty:
        logging.debug(f"{symbol}: Encontradas {len(df_abertas)} posição(ões) aberta(s).")
        return symbol, df_abertas
    else:
        logging.debug(f"{symbol}: Nenhuma posição aberta.")
    return None

def main():
    logging.info("Iniciando verificação de posições abertas em todos os pares...")
    resultados = []
    # Utiliza 10 threads para processar os pares em paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futuros = {executor.submit(process_symbol, symbol): symbol for symbol in TRADING_PAIRS}
        for future in concurrent.futures.as_completed(futuros):
            res = future.result()
            if res:
                resultados.append(res)

    if resultados:
        for symbol, df in resultados:
            print(f"\nPosições abertas para {symbol}:")
            print(df.to_string(index=False))
    else:
        print("Nenhuma posição aberta encontrada.")

if __name__ == "__main__":
    main()
