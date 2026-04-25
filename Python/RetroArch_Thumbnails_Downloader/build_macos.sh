#!/bin/bash

echo "Building RetroArch Thumbnails Downloader for macOS..."

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
echo "Building application bundle..."
pyinstaller retro_thumbnails.spec --clean --noconfirm

# Create dist directory if it doesn't exist
mkdir -p dist/macos

# Copy app bundle to dist directory
if [ -d "dist/RetroArch Thumbnails Downloader.app" ]; then
    cp -r "dist/RetroArch Thumbnails Downloader.app" "dist/macos/"
    echo "Build completed successfully!"
    echo "Application bundle located at: dist/macos/RetroArch Thumbnails Downloader.app"
else
    echo "Build failed!"
fi

# Deactivate virtual environment
deactivate
