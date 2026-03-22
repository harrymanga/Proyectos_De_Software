#!/usr/bin/env python3
"""
Build Script for Windows Executable (.exe)
Uses PyInstaller to create standalone Windows executable
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🗑️  Cleaning {dir_name}/...")
            shutil.rmtree(dir_name)
    
    # Clean spec file
    spec_file = 'JarTool_windows.spec'
    if os.path.exists(spec_file):
        os.remove(spec_file)


def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False


def install_pyinstaller():
    """Install PyInstaller"""
    print("📦 Installing PyInstaller...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])


def create_windows_build():
    """Create Windows executable using PyInstaller"""
    print("🪟 Building Windows executable...")
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=JarTool',
        '--windowed',  # No console window
        '--onefile',   # Single executable file
        '--clean',     # Clean cache
        '--noconfirm', # Overwrite existing
        # Add data files
        '--add-data=translations;translations',
        # Hidden imports
        '--hidden-import=PyQt6.sip',
        '--hidden-import=core.jar_handler',
        '--hidden-import=core.theme_manager',
        '--hidden-import=core.language_manager',
        '--hidden-import=gui.main_window',
        '--hidden-import=gui.ui_main_window',
        '--hidden-import=gui.worker_thread',
        # Exclude unnecessary modules
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=PIL',
        '--exclude-module=scipy',
        '--exclude-module=sklearn',
        # Icon (optional - add when available)
        # '--icon=icons/jartool.ico',
        # Upx compression
        '--upx-dir=upx',
        # Main script
        'main/main.py'
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✅ Windows build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False


def package_windows():
    """Package Windows executable with installer script"""
    print("📦 Packaging Windows executable...")
    
    # Create distribution directory
    dist_dir = 'dist/JarTool_windows'
    os.makedirs(dist_dir, exist_ok=True)
    
    # Copy executable
    exe_source = 'dist/JarTool.exe'
    exe_dest = os.path.join(dist_dir, 'JarTool.exe')
    
    if os.path.exists(exe_source):
        shutil.copy2(exe_source, exe_dest)
        print(f"✅ Copied: {exe_source} -> {exe_dest}")
    else:
        print(f"❌ Executable not found: {exe_source}")
        return False
    
    # Copy translations
    translations_src = 'translations'
    translations_dest = os.path.join(dist_dir, 'translations')
    if os.path.exists(translations_src):
        shutil.copytree(translations_src, translations_dest, dirs_exist_ok=True)
        print(f"✅ Copied translations")
    
    # Create README
    readme_content = """# JarTool for Windows

## Installation
1. Extract all files from this archive
2. Run `JarTool.exe`

## Features
- Extract JAR files
- Create JAR files from folders
- Multi-language support (EN, ES, FR, DE, PT)
- Dark/Light themes
- Batch processing

## Requirements
- Windows 10 or later
- No additional dependencies needed (standalone executable)

## Support
For issues and feature requests, please contact the developer.
"""
    with open(os.path.join(dist_dir, 'README.txt'), 'w') as f:
        f.write(readme_content)
    
    # Create batch file for quick launch
    batch_content = """@echo off
echo Starting JarTool...
start "" "%~dp0JarTool.exe"
"""
    with open(os.path.join(dist_dir, 'Start JarTool.bat'), 'w') as f:
        f.write(batch_content)
    
    print(f"✅ Windows package created: {dist_dir}/")
    print(f"📊 Size: {get_dir_size(dist_dir):.1f} MB")
    
    return True


def get_dir_size(path):
    """Get directory size in MB"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return total / (1024 * 1024)


def main():
    """Main build process for Windows"""
    print("🚀 JarTool Windows Build Script")
    print("=" * 50)
    
    # Check if we're on Windows (or building for Windows from another OS)
    if sys.platform == 'win32':
        print("✅ Running on Windows")
    else:
        print("⚠️  Not running on Windows - cross-compilation may have issues")
        print("   For best results, run this script on Windows")
    
    # Check PyInstaller
    if not check_pyinstaller():
        print("⚠️  PyInstaller not found")
        response = input("Install PyInstaller? (y/n): ")
        if response.lower() == 'y':
            install_pyinstaller()
        else:
            print("❌ PyInstaller required. Exiting.")
            return 1
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build executable
    if not create_windows_build():
        return 1
    
    # Package
    if not package_windows():
        return 1
    
    print("\n" + "=" * 50)
    print("✅ Windows build completed!")
    print(f"📁 Output: dist/JarTool_windows/")
    print("📝 Files included:")
    print("   - JarTool.exe (standalone executable)")
    print("   - translations/ (language files)")
    print("   - README.txt (instructions)")
    print("   - Start JarTool.bat (quick launcher)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
