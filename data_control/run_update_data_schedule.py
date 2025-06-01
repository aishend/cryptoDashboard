#!/usr/bin/env python3
import schedule
import time
import subprocess
import sys
import os

def run_update():
    venv_python = "/home/leandro/cryptoDashboard/.venv/bin/python"
    script_path = "/home/leandro/cryptoDashboard/data_control/update_data.py"
    print(f"Rodando update_data.py às {time.strftime('%Y-%m-%d %H:%M:%S')}")
    subprocess.run([venv_python, script_path])

# Agenda para rodar a cada 30 minutos
schedule.every(30).minutes.do(run_update)

# Rode uma vez no início, como no boot
run_update()

while True:
    schedule.run_pending()
    time.sleep(10)
