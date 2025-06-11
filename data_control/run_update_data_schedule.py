#!/usr/bin/env python3
import schedule
import time
import subprocess
import os

VENV_PYTHON = "/home/leandro/cryptoDashboard/.venv/bin/python"
DATA_CONTROL = "/home/leandro/cryptoDashboard/data_control"

def update_trading_pairs():
    print("Rodando update_trading_pairs.py")
    subprocess.run([VENV_PYTHON, f"{DATA_CONTROL}/update_trading_pairs.py"])

def update_data():
    print("Rodando update_data.py")
    subprocess.run([VENV_PYTHON, f"{DATA_CONTROL}/update_data.py"])

# Roda update_trading_pairs.py a cada 24 horas (a partir do momento em que o script iniciar)
schedule.every(24).hours.do(update_trading_pairs)

# Roda update_data.py a cada 30 minutos
schedule.every(15).minutes.do(update_data)

# (Opcional) Rode ambos no início
update_trading_pairs()
update_data()

while True:
    schedule.run_pending()