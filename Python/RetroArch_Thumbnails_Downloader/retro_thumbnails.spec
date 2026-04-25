# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('locales', 'locales'),
        ('ui', 'ui'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'requests',
        'json',
        'os',
        'sys',
        'glob',
        'threading',
        'urllib.parse',
    ],
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
