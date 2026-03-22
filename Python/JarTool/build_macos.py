#!/usr/bin/env python3
"""
Build Script for macOS App Bundle (.app)
Creates macOS application bundle using PyInstaller
"""

import os
import sys
import shutil
import subprocess
import plistlib
from pathlib import Path


def check_dependencies():
    """Check if required tools are installed"""
    if sys.platform != 'darwin':
        print("⚠️  Not running on macOS")
        print("   macOS builds should be created on a Mac")
        return False
    
    try:
        import PyInstaller
        return True
    except ImportError:
        print("❌ PyInstaller not installed")
        print("📦 Install with: pip install pyinstaller")
        return False


def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🗑️  Cleaning {dir_name}/...")
            shutil.rmtree(dir_name)


def create_info_plist():
    """Create Info.plist for macOS app bundle"""
    plist = {
        'CFBundleDevelopmentRegion': 'en',
        'CFBundleExecutable': 'JarTool',
        'CFBundleIconFile': 'jartool.icns',
        'CFBundleIdentifier': 'com.jartool.app',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundleName': 'JarTool',
        'CFBundlePackageType': 'APPL',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'CFBundleSignature': 'JART',
        'LSMinimumSystemVersion': '10.13',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSApplicationCategoryType': 'public.app-category.developer-tools',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeExtensions': ['jar'],
                'CFBundleTypeIconFile': 'jar.icns',
                'CFBundleTypeName': 'JAR Archive',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': ['com.sun.java-archive']
            }
        ],
        'UTExportedTypeDeclarations': [
            {
                'UTTypeIdentifier': 'com.sun.java-archive',
                'UTTypeDescription': 'JAR Archive',
                'UTTypeConformsTo': ['public.archive', 'public.data'],
                'UTTypeTagSpecification': {
                    'public.filename-extension': ['jar'],
                    'public.mime-type': ['application/java-archive']
                }
            }
        ]
    }
    
    return plist


def create_entitlements():
    """Create entitlements file for code signing"""
    entitlements = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
</plist>
"""
    with open('entitlements.plist', 'w') as f:
        f.write(entitlements)
    print("✅ Created entitlements.plist")


def build_macos_app():
    """Build macOS app bundle using PyInstaller"""
    print("🍎 Building macOS app bundle...")
    
    # PyInstaller command for macOS
    cmd = [
        'pyinstaller',
        '--name=JarTool',
        '--windowed',  # GUI app (no console)
        '--onefile',   # Single file (for internal executable)
        '--clean',
        '--noconfirm',
        # macOS specific
        '--osx-bundle-identifier=com.jartool.app',
        '--target-arch=x86_64',  # Build for Intel Macs
        # '--target-arch=arm64',  # Uncomment for Apple Silicon
        # Data files
        '--add-data=translations:translations',
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
        # Main script
        'main/main.py'
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✅ PyInstaller build completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False


def create_proper_app_bundle():
    """Create proper macOS .app bundle structure"""
    print("🏗️  Creating app bundle structure...")
    
    app_name = 'JarTool.app'
    app_path = f'dist/{app_name}'
    contents_path = f'{app_path}/Contents'
    macos_path = f'{contents_path}/MacOS'
    resources_path = f'{contents_path}/Resources'
    frameworks_path = f'{contents_path}/Frameworks'
    
    # Create directory structure
    for path in [macos_path, resources_path, frameworks_path]:
        os.makedirs(path, exist_ok=True)
    
    # Create Info.plist
    plist = create_info_plist()
    with open(f'{contents_path}/Info.plist', 'wb') as f:
        plistlib.dump(plist, f)
    print("✅ Created Info.plist")
    
    # Move executable
    exe_source = 'dist/JarTool'
    exe_dest = f'{macos_path}/JarTool'
    
    if os.path.exists(exe_source):
        shutil.move(exe_source, exe_dest)
        os.chmod(exe_dest, 0o755)
        print(f"✅ Moved executable to {exe_dest}")
    else:
        # Try alternate location
        exe_source = 'dist/JarTool.app/Contents/MacOS/JarTool'
        if os.path.exists(exe_source):
            shutil.copy2(exe_source, exe_dest)
            os.chmod(exe_dest, 0o755)
        else:
            print(f"❌ Executable not found")
            return False
    
    # Copy translations
    if os.path.exists('translations'):
        shutil.copytree('translations', f'{resources_path}/translations', dirs_exist_ok=True)
        print("✅ Copied translations")
    
    # Create PkgInfo
    with open(f'{contents_path}/PkgInfo', 'w') as f:
        f.write('APPLJART')
    print("✅ Created PkgInfo")
    
    # Create icon if available
    # TODO: Add proper .icns file
    
    return True


def create_dmg():
    """Create DMG installer for distribution"""
    print("💿 Creating DMG installer...")
    
    # Check if create-dmg is installed
    if shutil.which('create-dmg'):
        return create_dmg_with_create_dmg()
    else:
        return create_dmg_with_hdiutil()


def create_dmg_with_hdiutil():
    """Create DMG using macOS hdiutil"""
    app_name = 'JarTool.app'
    dmg_name = 'JarTool-2.0.0-macos.dmg'
    temp_dmg = 'temp.dmg'
    
    try:
        # Create temporary DMG
        cmd = [
            'hdiutil', 'create',
            '-srcfolder', 'dist',
            '-volname', 'JarTool',
            '-fs', 'HFS+',
            '-format', 'UDRW',
            temp_dmg
        ]
        subprocess.check_call(cmd)
        
        # Mount DMG for customization
        mount_result = subprocess.check_output(['hdiutil', 'attach', '-nobrowse', temp_dmg]).decode()
        mount_point = None
        for line in mount_result.split('\n'):
            if '/Volumes/' in line:
                parts = line.split('\t')
                for part in parts:
                    if '/Volumes/' in part:
                        mount_point = part.strip()
                        break
        
        if mount_point:
            # Create alias to Applications folder
            apps_link = os.path.join(mount_point, 'Applications')
            if not os.path.exists(apps_link):
                os.symlink('/Applications', apps_link)
            
            # Unmount
            subprocess.check_call(['hdiutil', 'detach', mount_point])
        
        # Convert to compressed read-only DMG
        cmd = [
            'hdiutil', 'convert',
            temp_dmg,
            '-format', 'UDZO',  # Compressed
            '-o', f'dist/{dmg_name}'
        ]
        subprocess.check_call(cmd)
        
        # Clean up
        os.remove(temp_dmg)
        
        print(f"✅ DMG created: dist/{dmg_name}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ DMG creation failed: {e}")
        return False


def create_dmg_with_create_dmg():
    """Create DMG using create-dmg tool"""
    dmg_name = 'JarTool-2.0.0-macos.dmg'
    
    cmd = [
        'create-dmg',
        '--volname', 'JarTool',
        '--window-pos', '200', '120',
        '--window-size', '600', '400',
        '--icon-size', '100',
        '--app-drop-link', '450', '185',
        '--icon', 'JarTool.app', '150', '185',
        f'dist/{dmg_name}',
        'dist/JarTool.app'
    ]
    
    try:
        subprocess.check_call(cmd)
        print(f"✅ DMG created: dist/{dmg_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ DMG creation failed: {e}")
        return False


def create_zip_bundle():
    """Create ZIP bundle as alternative"""
    print("📦 Creating ZIP bundle...")
    
    zip_name = 'dist/JarTool-macos.zip'
    
    try:
        # Create ZIP of the app
        subprocess.check_call([
            'zip', '-ry', zip_name, 'dist/JarTool.app'
        ])
        
        print(f"✅ ZIP created: {zip_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ZIP creation failed: {e}")
        return False


def code_sign_app():
    """Code sign the application (optional)"""
    print("🔏 Code signing...")
    
    app_path = 'dist/JarTool.app'
    
    # Check if we have a signing identity
    try:
        result = subprocess.check_output(['security', 'find-identity', '-v', '-p', 'codesigning']).decode()
        if '0 valid identities found' in result:
            print("⚠️  No code signing identities found")
            print("   Skipping code signing (app will still work)")
            return False
        
        # Sign with ad-hoc signature (works for local use)
        cmd = ['codesign', '--force', '--deep', '--sign', '-', app_path]
        subprocess.check_call(cmd)
        print("✅ Ad-hoc code signing completed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Code signing skipped: {e}")
        return False


def verify_app():
    """Verify the app bundle"""
    print("🔍 Verifying app bundle...")
    
    app_path = 'dist/JarTool.app'
    
    # Check structure
    required_paths = [
        f'{app_path}/Contents/Info.plist',
        f'{app_path}/Contents/MacOS/JarTool',
    ]
    
    for path in required_paths:
        if os.path.exists(path):
            print(f"✅ {path}")
        else:
            print(f"❌ Missing: {path}")
            return False
    
    return True


def main():
    """Main build process for macOS"""
    print("🍎 JarTool macOS Build Script")
    print("=" * 50)
    
    if sys.platform != 'darwin':
        print("❌ Not running on macOS")
        print("   macOS builds must be created on a Mac")
        print("   Alternative: Use GitHub Actions with macOS runner")
        return 1
    
    # Check dependencies
    if not check_dependencies():
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return 1
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create entitlements
    create_entitlements()
    
    # Build with PyInstaller
    if not build_macos_app():
        return 1
    
    # Create proper app bundle
    if not create_proper_app_bundle():
        return 1
    
    # Verify
    if not verify_app():
        return 1
    
    # Code sign (optional)
    code_sign_app()
    
    # Create distribution packages
    dmg_success = create_dmg()
    zip_success = create_zip_bundle()
    
    print("\n" + "=" * 50)
    print("✅ macOS build completed!")
    print("\n📁 Output files:")
    print("   - dist/JarTool.app (app bundle)")
    
    if dmg_success:
        print("   - dist/JarTool-2.0.0-macos.dmg (installer)")
    
    if zip_success:
        print("   - dist/JarTool-macos.zip (portable)")
    
    print("\n📝 Installation:")
    print("   DMG:   Open DMG, drag app to Applications")
    print("   ZIP:   Extract, move app to Applications")
    print("   App:   Directly run JarTool.app")
    
    print("\n⚠️  First run:")
    print("   If 'App can't be opened' appears:")
    print("   1. Right-click app -> Open")
    print("   2. Or: System Preferences -> Security -> Open Anyway")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
