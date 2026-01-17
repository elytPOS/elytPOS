# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None
base_path = os.getcwd()

# Define datas list
added_datas = [
    (os.path.join(base_path, 'splash.png'), '.'), (os.path.join(base_path, 'logo.svg'), '.')
]

# Only bundle XKB data on Linux
if sys.platform.startswith('linux'):
    added_datas.append(('/usr/share/X11/xkb', 'xkb_data'))

a = Analysis(
    ['main.py'],
    pathex=[base_path],
    binaries=[],
    datas=added_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='elytPOS',
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
)
