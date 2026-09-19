@echo off
REM run.bat — Punto de entrada único en Windows: crea .venv, instala y ejecuta.
REM Uso: run.bat [args de appimage-builder]
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>&1
    if %errorlevel%==0 ( py -3 -m venv .venv ) else ( python -m venv .venv )
)
".venv\Scripts\python.exe" -m pip install -q --upgrade pip
".venv\Scripts\python.exe" -m pip install -q -e .
".venv\Scripts\appimage-builder.exe" %*
