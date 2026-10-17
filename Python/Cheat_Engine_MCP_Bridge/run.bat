@echo off
REM run.bat — Punto de entrada único en Windows: crea .venv e instala deps.
REM Uso: run.bat
REM Nota: el arranque (.sh) es bash; en Windows usa Git Bash y ejecuta
REM mcp_cheatengine_start.sh con el venv ya creado por este script.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>&1
    if %errorlevel%==0 ( py -3 -m venv .venv ) else ( python -m venv .venv )
)
".venv\Scripts\python.exe" -m pip install -q --upgrade pip
".venv\Scripts\python.exe" -m pip install -q -e .
where bash >nul 2>&1
if %errorlevel%==0 (
    bash mcp_cheatengine_start.sh %*
) else (
    echo Instala Git Bash y ejecuta: bash mcp_cheatengine_start.sh
)
