#!/usr/bin/env python3
import schedule
import time
import subprocess
import os

VENV_PYTHON = "/home/leandro/cryptoDashboard/.venv/bin/python"
DATA_CONTROL = "/home/leandro/cryptoDashboard/data_control"

def run_update_pairs():
    print("Rodando update_trading_pairs.py")
    subprocess.run([VENV_PYTHON, os.path.join(DATA_CONTROL, "update_trading_pairs.py")])

def run_update_data():
    print("Rodando update_data.py")
    subprocess.run([VENV_PYTHON, os.path.join(DATA_CONTROL, "update_data.py")])

# No boot: roda update_trading_pairs e update_data
run_update_pairs()
run_update_data()

# Agenda update_data.py a cada 30 minutos
schedule.every(30).minutes.do(run_update_data)

while True:
    schedule.run_pending()
    time.sleep(10)
