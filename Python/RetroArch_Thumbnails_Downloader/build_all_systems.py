#!/usr/bin/env python3
"""
Script de compilación unificado para Retro Arch Thumbnails Downloader
Admite la compilación para Windows, Linux y Mac OS

Unified build script for RetroArch Thumbnails Downloader
Supports building for Windows, Linux, and macOS
"""

import os
import sys
import platform
import subprocess
import shutil


def check_virtual_env():
    """Compruebe si existe un entorno virtual, créelo si no"""
    """Check if virtual environment exists, create if not"""
    if not os.path.exists("venv"):
        print("Creando un entorno virtual...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)


def activate_venv():
    """Devuelve la ruta al Python del entorno virtual"""
    """Return the path to the virtual environment's python"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "python.exe")
    else:
        return os.path.join("venv", "bin", "python")


def install_dependencies(venv_python):
    """Instala las dependencias desde requirements.txt"""
    """Install dependencies from requirements.txt"""
    print("Instalando dependencias...")
    subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    subprocess.run([venv_python, "-m", "pip", "install", "pyinstaller"], check=True)


def build(venv_python):
    """Compila la aplicación usando PyInstaller"""
    """Build the application using PyInstaller"""
    print("Compilando aplicación...")
    subprocess.run([venv_python, "-m", "PyInstaller", "retro_thumbnails.spec", "--clean", "--noconfirm"], check=True)


def copy_build_output():
    """Copia la salida de la compilación al directorio apropiado para la plataforma"""
    """Copy build output to appropriate platform directory"""
    system = platform.system()
    
    # Create platform-specific directory
    if system == "Windows":
        dist_dir = "dist/windows"
        source = "dist/RetroArch Thumbnails Downloader.exe"
    elif system == "Darwin":
        dist_dir = "dist/macos"
        source = "dist/RetroArch Thumbnails Downloader.app"
    else:  # Linux
        dist_dir = "dist/linux"
        source = "dist/RetroArch Thumbnails Downloader"
    
    os.makedirs(dist_dir, exist_ok=True)
    
    if os.path.exists(source):
        if os.path.isdir(source):
            shutil.copytree(source, os.path.join(dist_dir, os.path.basename(source)), dirs_exist_ok=True)
        else:
            shutil.copy2(source, dist_dir)
        
        # Make executable on Linux/macOS
        if system != "Windows":
            executable = os.path.join(dist_dir, os.path.basename(source))
            if os.path.isfile(executable):
                os.chmod(executable, 0o755)
        
        print(f"Compilación completada exitosamente!")
        print(f"Salida ubicada en: {dist_dir}/{os.path.basename(source)}")
    else:
        print("¡La compilación falló!")
        sys.exit(1)


def main():
    """Función principal de compilación"""
    """Main build function"""
    print(f"Compilando RetroArch Thumbnails Downloader para {platform.system()}...")
    
    # Check and create virtual environment
    check_virtual_env()
    
    # Get venv python path
    venv_python = activate_venv()
    
    # Install dependencies
    install_dependencies(venv_python)
    
    # Build application
    build(venv_python)
    
    # Copy build output
    copy_build_output()


if __name__ == "__main__":
    main()
