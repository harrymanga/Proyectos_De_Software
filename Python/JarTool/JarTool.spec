# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for JarTool
Generates executables for Windows, Linux, and macOS
"""

import os
import sys

# Project root
project_root = os.path.abspath(os.path.dirname(__file__))

# Data files to include
data_files = [
    # Translations
    ('translations/*.json', 'translations'),
    # Icons (if any)
    # ('icons/*.png', 'icons'),
    # ('icons/*.ico', 'icons'),
]

# Hidden imports (modules that PyInstaller might miss)
hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'core',
    'core.jar_handler',
    'core.theme_manager',
    'core.language_manager',
    'gui',
    'gui.main_window',
    'gui.ui_main_window',
    'gui.worker_thread',
]

# Analysis configuration
a = Analysis(
    ['main/main.py'],
    pathex=[project_root],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'scipy',
        'sklearn',
        'tensorflow',
        'torch',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

# Remove duplicates
pyz = PYZ(a.pure, a.zipped_data)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JarTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows specific
    icon=None,  # Add 'icons/jartool.ico' when available
)

# macOS app bundle
app = BUNDLE(
    exe,
    name='JarTool.app',
    icon=None,  # Add 'icons/jartool.icns' when available
    bundle_identifier='com.jartool.app',
    info_plist={
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',
        'CFBundleDisplayName': 'JarTool',
        'CFBundleName': 'JarTool',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'JART',
        'LSMinimumSystemVersion': '10.13',
        'NSRequiresAquaSystemAppearance': 'False',
    },
)
