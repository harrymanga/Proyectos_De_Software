@echo off
echo Construyendo RetroArch Thumbnails Downloader para Windows...

:: Check if virtual environment exists
if not exist "venv" (
    echo Creando un entorno virtual...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install dependencies
echo Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

:: Build with PyInstaller
echo Construyendo ejecutable...
python -m PyInstaller retro_thumbnails.spec --clean --noconfirm

:: Create dist directory if it doesn't exist
if not exist "dist\windows" mkdir dist\windows

:: Copy executable to dist directory
if exist "dist\RetroArch Thumbnails Downloader.exe" (
    copy "dist\RetroArch Thumbnails Downloader.exe" "dist\windows\"
    echo ¡Construccion completada con exito!
    echo Ejecutable ubicado en: dist\windows\RetroArch Thumbnails Downloader.exe
) else (
    echo ¡Error de construccion!
)

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat

pause
