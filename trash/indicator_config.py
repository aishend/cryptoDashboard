# indicator_config.py

# Configurações individuais para cada indicador em cada timeframe.
# Você pode alterar os parâmetros abaixo conforme sua necessidade.
INDICATOR_CONFIG = {
    "1h": {
         "RSI": {"length": 14},
         "StochRSI": {"rsi_length": 14, "k": 3, "d": 3},
         "MACD": {"fast_length": 12, "slow_length": 26, "signal_length": 9},
         "MACDZeroLag": {"fast_length": 12, "slow_length": 24, "signal_length": 9},
         "Stochastic": {"periodK": 14, "smoothK": 3, "periodD": 3}
    },
    "4h": {
         "RSI": {"length": 14},
         "StochRSI": {"rsi_length": 14, "k": 3, "d": 3},
         "MACD": {"fast_length": 12, "slow_length": 26, "signal_length": 9},
         "MACDZeroLag": {"fast_length": 12, "slow_length": 24, "signal_length": 9},
         "Stochastic": {"periodK": 5, "smoothK": 3, "periodD": 3}
    },
    "1d": {
         "RSI": {"length": 14},
         "StochRSI": {"rsi_length": 14, "k": 3, "d": 3},
         "MACD": {"fast_length": 12, "slow_length": 26, "signal_length": 9},
         "MACDZeroLag": {"fast_length": 12, "slow_length": 24, "signal_length": 9},
         "Stochastic": {"periodK": 5, "smoothK": 3, "periodD": 3}
    }
}
