from binance_client import get_futures_balance, get_futures_open_orders, get_futures_positions
from trading_pairs1 import TRADING_PAIRS

def monitor_futures(symbol=None):
    if symbol is None:
        symbol = TRADING_PAIRS[0]

    orders_df = get_futures_open_orders(symbol)
    positions_df = get_futures_positions(symbol)
    balance_df = get_futures_balance()

    if orders_df.empty and positions_df.empty:
        print(f"Não há ordens ou posições abertas no mercado Futures para {symbol}.")
    else:
        if not orders_df.empty:
            print(f"Ordens abertas no Futures ({symbol}):")
            print(orders_df)
        if not positions_df.empty:
            print(f"Posições no Futures ({symbol}):")
            print(positions_df)
    
    if not balance_df.empty:
        print("Saldo da conta Futures:")
        print(balance_df)
