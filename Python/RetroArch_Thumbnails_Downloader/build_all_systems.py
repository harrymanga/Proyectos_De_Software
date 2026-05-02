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
        try:
            result = subprocess.run([sys.executable, "-m", "venv", "venv"], 
                                  check=True, capture_output=True, text=True)
            print("Entorno virtual creado exitosamente.")
            
            # Verificar que se crearon los archivos necesarios
            if platform.system() == "Windows":
                scripts_dir = os.path.join("venv", "Scripts")
                python_exe = os.path.join(scripts_dir, "python.exe")
            else:
                scripts_dir = os.path.join("venv", "bin")
                python_exe = os.path.join(scripts_dir, "python")
            
            if not os.path.exists(python_exe):
                print(f"Error: No se encontró Python en el entorno virtual: {python_exe}")
                print("El entorno virtual no se creó correctamente.")
                sys.exit(1)
                
        except subprocess.CalledProcessError as e:
            print(f"Error al crear el entorno virtual: {e}")
            print(f"Stderr: {e.stderr}")
            sys.exit(1)
    else:
        print("El entorno virtual ya existe.")


def activate_venv():
    """Devuelve la ruta al Python del entorno virtual"""
    """Return the path to the virtual environment's python"""
    if platform.system() == "Windows":
        venv_python = os.path.join("venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join("venv", "bin", "python")
    
    # Verificar si el ejecutable existe
    if not os.path.exists(venv_python):
        print(f"Error: No se encuentra el ejecutable de Python en: {venv_python}")
        print("El entorno virtual no se creó correctamente o está incompleto.")
        sys.exit(1)
    
    return venv_python


def install_dependencies(venv_python):
    """Instala las dependencias desde requirements.txt"""
    """Install dependencies from requirements.txt"""
    print("Instalando dependencias...")
    try:
        # Actualizar pip primero
        print("Actualizando pip...")
        subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True, text=True)
        
        # Instalar dependencias
        print("Instalando requirements.txt...")
        result = subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], 
                               check=True, capture_output=True, text=True)
        print("Dependencias instaladas exitosamente.")
        
        # Instalar PyInstaller
        print("Instalando PyInstaller...")
        result = subprocess.run([venv_python, "-m", "pip", "install", "pyinstaller"], 
                               check=True, capture_output=True, text=True)
        print("PyInstaller instalado exitosamente.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error al instalar dependencias: {e}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        sys.exit(1)


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
