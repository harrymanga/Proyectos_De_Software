@echo off
:: Lanzador para Windows
:: Crea el entorno virtual, instala dependencias y ejecuta la aplicación.
:: Norma §56: arranque sin fricción.

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "VENV_DIR=.venv"
set "PYTHON_CMD=python"

echo [Mod_Maker] Iniciando lanzador en Windows...

:: Crear entorno virtual si no existe
if not exist "%VENV_DIR%\" (
    echo [Mod_Maker] Creando entorno virtual en %VENV_DIR%...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
)

:: Activar entorno virtual
call "%VENV_DIR%\Scripts\activate.bat"

:: Instalar dependencias
if exist requirements.txt (
    echo [Mod_Maker] Instalando dependencias desde requirements.txt...
    pip install --upgrade pip
    pip install -r requirements.txt
)

:: Resolver paquetes del sistema si existen
if exist system-packages.txt (
    echo [Mod_Maker] Revisando paquetes del sistema declarados en system-packages.txt...
    for /f "usebackq delims=" %%p in (system-packages.txt) do (
        set "pkg=%%p"
        if not "!pkg:~0,1!"="#" if defined pkg (
            echo [Mod_Maker] Paquete del sistema declarado: !pkg! (instalación manual si es necesario)
        )
    )
)

:: Ejecutar la aplicación
echo [Mod_Maker] Ejecutando Mod_Maker...
python -m src.gui.main_window

endlocal
