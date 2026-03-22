#!/usr/bin/env python3
"""
Build Script for Linux AppImage
Creates portable Linux AppImage using appimage-builder
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path


def check_dependencies():
    """Check if required build tools are installed"""
    deps = {
        'PyInstaller': 'pyinstaller',
        'appimagetool': 'appimagetool',
    }
    
    missing = []
    for name, cmd in deps.items():
        if not shutil.which(cmd):
            missing.append(name)
    
    if missing:
        print("❌ Missing dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print("\n📦 Install with:")
        print("   pip install pyinstaller")
        print("   # Download appimagetool from:")
        print("   # https://github.com/AppImage/AppImageKit/releases")
        return False
    
    return True


def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', 'AppDir', 'appimage-build']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🗑️  Cleaning {dir_name}/...")
            shutil.rmtree(dir_name)


def create_desktop_file():
    """Create .desktop file for AppImage"""
    desktop_content = """[Desktop Entry]
Name=JarTool
Exec=jartool
Icon=jartool
Type=Application
Categories=Development;Utility;
Comment=Extract and compress JAR files
Terminal=false
StartupNotify=true
MimeType=application/java-archive;
"""
    
    os.makedirs('AppDir/usr/share/applications', exist_ok=True)
    with open('AppDir/usr/share/applications/jartool.desktop', 'w') as f:
        f.write(desktop_content)
    
    # Copy to root of AppDir
    with open('AppDir/jartool.desktop', 'w') as f:
        f.write(desktop_content)
    
    print("✅ Created .desktop file")


def create_app_run():
    """Create AppRun script for AppImage"""
    apprun_content = """#!/bin/bash
# AppRun script for JarTool AppImage

# Get the directory where this AppRun is located
APPDIR="$(dirname "$(readlink -f "$0")")"

# Set up environment
export PATH="$APPDIR/usr/bin:$PATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"

# Run the application
exec "$APPDIR/usr/bin/JarTool" "$@"
"""
    
    with open('AppDir/AppRun', 'w') as f:
        f.write(apprun_content)
    
    # Make executable
    os.chmod('AppDir/AppRun', 0o755)
    print("✅ Created AppRun script")


def create_build_environment():
    """Create AppDir structure for AppImage"""
    print("🏗️  Creating AppDir structure...")
    
    # Create directory structure
    dirs = [
        'AppDir/usr/bin',
        'AppDir/usr/lib',
        'AppDir/usr/share/applications',
        'AppDir/usr/share/icons/hicolor/256x256/apps',
        'AppDir/translations',
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    # Create desktop and AppRun files
    create_desktop_file()
    create_app_run()


def build_executable():
    """Build executable using PyInstaller"""
    print("🔨 Building Linux executable...")
    
    cmd = [
        'pyinstaller',
        '--name=JarTool',
        '--windowed',
        '--onefile',
        '--clean',
        '--noconfirm',
        '--distpath=AppDir/usr/bin',
        '--add-data=translations:translations',
        '--hidden-import=PyQt6.sip',
        '--hidden-import=core.jar_handler',
        '--hidden-import=core.theme_manager',
        '--hidden-import=core.language_manager',
        '--hidden-import=gui.main_window',
        '--hidden-import=gui.ui_main_window',
        '--hidden-import=gui.worker_thread',
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=PIL',
        '--exclude-module=scipy',
        'main/main.py'
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✅ Executable built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False


def copy_resources():
    """Copy resources to AppDir"""
    print("📦 Copying resources...")
    
    # Copy translations
    if os.path.exists('translations'):
        shutil.copytree('translations', 'AppDir/translations', dirs_exist_ok=True)
        print("✅ Copied translations")
    
    # Create placeholder icon
    # TODO: Replace with actual icon
    icon_path = 'AppDir/usr/share/icons/hicolor/256x256/apps/jartool.png'
    # Create a simple placeholder or copy existing
    if not os.path.exists(icon_path):
        # Create empty placeholder
        open(icon_path, 'a').close()


def create_appimage_builder_config():
    """Create appimage-builder configuration"""
    config = {
        "version": 1,
        "AppDir": {
            "path": "./AppDir",
            "app_info": {
                "id": "com.jartool.app",
                "name": "JarTool",
                "icon": "jartool",
                "version": "2.0.0",
                "exec": "usr/bin/JarTool",
                "exec_args": "$@"
            },
            "apt": {
                "arch": ["amd64"],
                "sources": [
                    {
                        "sourceline": "deb http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse",
                        "key_url": "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3b4fe6acc0b21f32"
                    }
                ],
                "include": [
                    "libqt5core5a",
                    "libqt5gui5",
                    "libqt5widgets5"
                ]
            },
            "files": {
                "include": [
                    "/usr/lib/x86_64-linux-gnu/libQt5*.so*",
                    "/usr/lib/x86_64-linux-gnu/libicu*.so*"
                ],
                "exclude": [
                    "usr/share/man",
                    "usr/share/doc",
                    "usr/share/locale"
                ]
            },
            "runtime": {
                "env": {
                    "APPDIR_LIBRARY_PATH": "$APPDIR/usr/lib"
                }
            }
        },
        "AppImage": {
            "arch": "x86_64",
            "comp": "xz",
            "update-information": "gh-releases-zsync|jartool|jartool|latest|*.AppImage.zsync",
            "sign-key": None
        }
    }
    
    with open('appimage-builder.yml', 'w') as f:
        # Write as YAML-like format
        f.write("""version: 1

script:
  - rm -rf AppDir || true
  - mkdir -p AppDir/usr/bin
  - cp dist/JarTool AppDir/usr/bin/
  - mkdir -p AppDir/translations
  - cp translations/*.json AppDir/translations/

AppDir:
  path: ./AppDir
  
  app_info:
    id: com.jartool.app
    name: JarTool
    icon: jartool
    version: 2.0.0
    exec: usr/bin/JarTool
    exec_args: $@

AppImage:
  arch: x86_64
  comp: xz
  update-information: None
  sign-key: None
""")
    
    print("✅ Created appimage-builder configuration")


def create_manual_appimage():
    """Create AppImage manually using appimagetool"""
    print("📦 Creating AppImage...")
    
    # Ensure AppDir exists
    if not os.path.exists('AppDir'):
        print("❌ AppDir not found. Run build steps first.")
        return False
    
    # Check for appimagetool
    appimagetool = shutil.which('appimagetool')
    if not appimagetool:
        print("❌ appimagetool not found")
        print("📥 Download from: https://github.com/AppImage/AppImageKit/releases")
        return False
    
    # Build AppImage
    output_name = 'JarTool-2.0.0-x86_64.AppImage'
    cmd = [appimagetool, 'AppDir', output_name]
    
    try:
        subprocess.check_call(cmd)
        print(f"✅ AppImage created: {output_name}")
        
        # Move to dist
        os.makedirs('dist', exist_ok=True)
        shutil.move(output_name, f'dist/{output_name}')
        
        # Make executable
        os.chmod(f'dist/{output_name}', 0o755)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ AppImage creation failed: {e}")
        return False


def create_alternative_bundle():
    """Create alternative portable tar.gz bundle"""
    print("📦 Creating portable tar.gz bundle...")
    
    bundle_dir = 'dist/JarTool_linux'
    os.makedirs(bundle_dir, exist_ok=True)
    
    # Copy executable
    exe_src = 'AppDir/usr/bin/JarTool'
    if os.path.exists(exe_src):
        shutil.copy2(exe_src, f'{bundle_dir}/JarTool')
        os.chmod(f'{bundle_dir}/JarTool', 0o755)
    else:
        print(f"❌ Executable not found: {exe_src}")
        return False
    
    # Copy translations
    if os.path.exists('translations'):
        shutil.copytree('translations', f'{bundle_dir}/translations', dirs_exist_ok=True)
    
    # Create launcher script
    launcher = f"""#!/bin/bash
# JarTool Launcher
cd "$(dirname "$(readlink -f "$0")")"
exec ./JarTool "$@"
"""
    with open(f'{bundle_dir}/run.sh', 'w') as f:
        f.write(launcher)
    os.chmod(f'{bundle_dir}/run.sh', 0o755)
    
    # Create README
    readme = """# JarTool for Linux

## Installation

### Option 1: AppImage (Recommended)
1. Download `JarTool-*.AppImage`
2. Make executable: `chmod +x JarTool-*.AppImage`
3. Run: `./JarTool-*.AppImage`

### Option 2: Portable Archive
1. Extract `JarTool_linux.tar.gz`
2. Run: `./run.sh` or `./JarTool`

## Features
- Extract JAR files
- Create JAR files from folders
- Multi-language support (EN, ES, FR, DE, PT, AR)
- Dark/Light themes
- Batch processing

## Requirements
- Linux x86_64
- Qt6 libraries (included in AppImage)

## Build from Source
See build_linux.py for build instructions.
"""
    with open(f'{bundle_dir}/README.txt', 'w') as f:
        f.write(readme)
    
    # Create tar.gz
    tar_name = 'dist/JarTool_linux.tar.gz'
    subprocess.check_call(['tar', '-czf', tar_name, '-C', 'dist', 'JarTool_linux'])
    
    print(f"✅ Portable bundle created: {tar_name}")
    size_mb = os.path.getsize(tar_name) / (1024 * 1024)
    print(f"📊 Size: {size_mb:.1f} MB")
    
    return True


def main():
    """Main build process for Linux"""
    print("🐧 JarTool Linux Build Script")
    print("=" * 50)
    
    if sys.platform != 'linux':
        print("⚠️  Not running on Linux")
        print("   This script should be run on Linux for best results")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return 1
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create build environment
    create_build_environment()
    
    # Build executable
    if not build_executable():
        return 1
    
    # Copy resources
    copy_resources()
    
    # Try to create AppImage
    appimage_success = create_manual_appimage()
    
    # Always create portable bundle as fallback
    if not create_alternative_bundle():
        return 1
    
    print("\n" + "=" * 50)
    print("✅ Linux build completed!")
    print("\n📁 Output files:")
    
    if appimage_success:
        print("   - dist/JarTool-2.0.0-x86_64.AppImage")
    
    print("   - dist/JarTool_linux.tar.gz (portable bundle)")
    print("\n📝 Installation:")
    print("   AppImage: chmod +x *.AppImage && ./*.AppImage")
    print("   Tar.gz:   tar -xzf *.tar.gz && ./JarTool_linux/run.sh")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
