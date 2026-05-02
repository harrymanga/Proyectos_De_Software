# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Recopilar todos los módulos, binarios y datos de PyQt5
pyqt5_datas, pyqt5_binaries, pyqt5_hiddenimports = collect_all('PyQt5')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=pyqt5_binaries,
    datas=[
        ('data', 'data'),
        ('locales', 'locales'),
        ('ui', 'ui'),
    ] + pyqt5_datas,
    hiddenimports=[
        'requests',
    ] + pyqt5_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RetroArch Thumbnails Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='data/icon.ico' if os.path.exists('data/icon.ico') else None,
)

# For macOS, create an app bundle instead of a single executable
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='RetroArch Thumbnails Downloader.app',
        icon='data/icon.icns' if os.path.exists('data/icon.icns') else None,
        bundle_identifier='com.retroarch.thumbnails.downloader',
        info_plist={
            'NSHighResolutionCapable': 'True',
        }
    )
