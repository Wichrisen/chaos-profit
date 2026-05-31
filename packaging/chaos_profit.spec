# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Хаос & Прибыль (Chaos & Profit)

This is a starting point. It will likely need adjustments as the game grows.

Usage:
    pyinstaller packaging/chaos_profit.spec
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path
import sys

block_cipher = None

project_root = Path.cwd()

# Include all assets
datas = [
    (str(project_root / "assets"), "assets"),
]

# Hidden imports that PyInstaller sometimes misses
hiddenimports = [
    "pygame",
    "pygame_gui",
]

a = Analysis(
    [str(project_root / "src" / "chaos_profit" / "ui_pygame" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='ChaosProfit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # Set to True if you want console window for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,               # TODO: Add path to .ico file later
)

# On macOS you can also create an .app bundle by uncommenting the following:
# app = BUNDLE(
#     exe,
#     name='Chaos & Profit.app',
#     icon=None,
#     bundle_identifier=None,
# )
