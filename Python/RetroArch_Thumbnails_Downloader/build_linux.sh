#!/bin/bash

echo "Building RetroArch Thumbnails Downloader for Linux..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

# Build with PyInstaller
echo "Building executable..."
pyinstaller retro_thumbnails.spec --clean --noconfirm

# Create dist directory if it doesn't exist
mkdir -p dist/linux

# Copy executable to dist directory
if [ -f "dist/RetroArch Thumbnails Downloader" ]; then
    cp "dist/RetroArch Thumbnails Downloader" "dist/linux/"
    chmod +x "dist/linux/RetroArch Thumbnails Downloader"
    echo "Build completed successfully!"
    echo "Executable located at: dist/linux/RetroArch Thumbnails Downloader"
else
    echo "Build failed!"
fi

# Deactivate virtual environment
deactivate
