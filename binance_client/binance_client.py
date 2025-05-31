import os
import nest_asyncio
nest_asyncio.apply()
# binance_client.py
import pandas as pd
from binance import Client, ThreadedWebsocketManager

# Lógica para carregar KEY e SECRET de variáveis de ambiente ou do config.py
KEY = os.environ.get('BINANCE_KEY')
SECRET = os.environ.get('BINANCE_SECRET')
if not KEY or not SECRET:
    try:
        from binance_client.config import KEY as FILE_KEY, SECRET as FILE_SECRET
        KEY = FILE_KEY
        SECRET = FILE_SECRET
    except ImportError:
        try:
            from config import KEY as FILE_KEY, SECRET as FILE_SECRET
            KEY = FILE_KEY
            SECRET = FILE_SECRET
        except ImportError:
            config_path = os.path.join(os.path.dirname(__file__), 'config.py')
            if not os.path.exists(config_path):
                with open(config_path, 'w') as f:
                    f.write('KEY = "COLOQUE_SUA_BINANCE_API_KEY_AQUI"\n')
                    f.write('SECRET = "COLOQUE_SUA_BINANCE_API_SECRET_AQUI"\n')
                print(f"Arquivo config.py criado em {config_path}. Coloque sua KEY e SECRET nele.")
            raise ImportError(f'Você precisa definir as variáveis de ambiente BINANCE_KEY e BINANCE_SECRET ou preencher o arquivo {config_path} com KEY e SECRET.')

import logging


logging.basicConfig(level=logging.INFO)
client = Client(KEY, SECRET)

def get_futures_klines(symbol: str, interval: str, lookback: str) -> pd.DataFrame:
    try:
        if isinstance(lookback, str):
            lookback_time = pd.to_datetime(lookback).timestamp() * 1000
        else:
            lookback_time = lookback
        raw_data = client.futures_klines(
            symbol=symbol,
            interval=interval,
            startTime=int(lookback_time)
        )
    except Exception as e:
        logging.error(f"Erro ao buscar dados de klines para Futures: {e}")
        return pd.DataFrame()
    if not raw_data:
        logging.warning("Nenhum dado retornado pela API para klines de Futures.")
        return pd.DataFrame()
    frame = pd.DataFrame(raw_data)
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def get_futures_open_orders(symbol: str) -> pd.DataFrame:
    try:
        orders = client.futures_get_open_orders(symbol=symbol)
    except Exception as e:
        logging.error(f"Erro ao buscar ordens abertas no Futures: {e}")
        return pd.DataFrame()
    return pd.DataFrame(orders) if orders else pd.DataFrame()

def get_futures_positions(symbol: str) -> pd.DataFrame:
    try:
        positions = client.futures_position_information(symbol=symbol)
    except Exception as e:
        logging.error(f"Erro ao buscar posições no Futures: {e}")
        return pd.DataFrame()
    return pd.DataFrame(positions) if positions else pd.DataFrame()

def get_funding_rate(symbol):
    try:
        funding = client.futures_funding_rate(symbol=symbol, limit=1)
        return float(funding[-1]["fundingRate"])
    except Exception as e:
        logging.error(f"Erro ao buscar taxa de financiamento: {e}")
        return None

def get_open_interest(symbol):
    try:
        oi = client.futures_open_interest(symbol=symbol)
        return float(oi["openInterest"])
    except Exception as e:
        logging.error(f"Erro ao buscar Open Interest: {e}")
        return None

def get_futures_balance():
    try:
        account_info = client.futures_account()
        balances = pd.DataFrame(account_info["assets"])
        return balances[["asset", "walletBalance", "unrealizedProfit", "marginBalance"]]
    except Exception as e:
        logging.error(f"Erro ao buscar saldo de Futures: {e}")
        return pd.DataFrame()

def get_futures_pairs():
    info = client.futures_exchange_info()
    # Pega apenas símbolos de contratos perpétuos ativos (os mais comuns)
    pairs = [
        s['symbol']
        for s in info['symbols']
        if s['status'] == 'TRADING' and s['contractType'] == 'PERPETUAL'
    ]
    return sorted(pairs)

# --- Websocket de Kline para futuros ---

# Dicionário global para armazenar dados de kline em tempo real
realtime_data = {}

def process_kline_message(msg):
    if msg.get('e') == 'kline':
        k = msg['k']
        if k.get('x'):  # vela fechada
            symbol = msg['s']
            dt = pd.to_datetime(k['t'], unit='ms')
            data = {
                "Open": float(k['o']),
                "High": float(k['h']),
                "Low": float(k['l']),
                "Close": float(k['c']),
                "Volume": float(k['v'])
            }
            if symbol not in realtime_data:
                realtime_data[symbol] = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
            realtime_data[symbol].loc[dt] = data
            logging.info(f"Realtime: {symbol} atualizado em {dt}")

def start_realtime_kline_socket(symbol: str, interval: str):
    """
    Inicia uma conexão websocket para receber dados de kline em tempo real para futuros.
    Constrói a string do stream (ex.: "btcusdt@kline_4h") e a passa em uma lista para o método
    start_futures_multiplex_socket.
    Retorna o objeto ThreadedWebsocketManager e a chave de conexão.
    """
    twm = ThreadedWebsocketManager(api_key=KEY, api_secret=SECRET)
    twm.start()
    stream = f"{symbol.lower()}@kline_{interval}"
    conn_key = twm.start_futures_multiplex_socket(process_kline_message, streams=[stream])
    logging.info(f"Websocket de kline iniciado para {symbol} no intervalo {interval} (stream: {stream})")
    return twm, conn_key


# --- Websocket de Usuário para dados da conta ---

realtime_account_data = {}

def process_user_message(msg):
    event_type = msg.get('e')
    if event_type == 'ACCOUNT_UPDATE':
        realtime_account_data['account_update'] = msg
        if 'a' in msg and 'P' in msg['a']:
            realtime_account_data['positions'] = msg['a']['P']
        logging.info("ACCOUNT_UPDATE recebido")
    elif event_type == 'ORDER_TRADE_UPDATE':
        realtime_account_data.setdefault('orders', []).append(msg)
        logging.info("ORDER_TRADE_UPDATE recebido")
    else:
        logging.info(f"Mensagem recebida: {msg}")

def start_realtime_user_socket():
    twm = ThreadedWebsocketManager(api_key=KEY, api_secret=SECRET)
    twm.start()
    conn_key = twm.start_futures_user_socket(callback=process_user_message)
    logging.info("Websocket de usuário iniciado")
    return twm, conn_key

