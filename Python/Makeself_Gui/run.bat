@echo off
if not exist .venv py -m venv .venv
.venv\Scripts\pip install -q -r requirements.txt
.venv\Scripts\python src\app.py %*
