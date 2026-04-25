@echo off
echo Building RetroArch Thumbnails Downloader for Windows...

:: Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

:: Build with PyInstaller
echo Building executable...
pyinstaller retro_thumbnails.spec --clean --noconfirm

:: Create dist directory if it doesn't exist
if not exist "dist\windows" mkdir dist\windows

:: Copy executable to dist directory
if exist "dist\RetroArch Thumbnails Downloader.exe" (
    copy "dist\RetroArch Thumbnails Downloader.exe" "dist\windows\"
    echo Build completed successfully!
    echo Executable located at: dist\windows\RetroArch Thumbnails Downloader.exe
) else (
    echo Build failed!
)

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat

pause
