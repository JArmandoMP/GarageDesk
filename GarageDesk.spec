# -*- mode: python ; coding: utf-8 -*-
"""Especificación de PyInstaller para GarageDesk 3.1.0.1.

Genera una carpeta (one-folder) con GarageDesk.exe + _internal.
El icono se copia a _internal para que la ventana lo encuentre.
"""
from PyInstaller.utils.hooks import collect_all

datas = [('Icono.ico', '.')]
binaries = []
hiddenimports = []

# CustomTkinter necesita sus assets (temas, fuentes, imágenes).
for modulo in ('customtkinter',):
    datos_modulo, bins_modulo, imports_modulo = collect_all(modulo)
    datas += datos_modulo
    binaries += bins_modulo
    hiddenimports += imports_modulo

a = Analysis(
    ['GarageDesk.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='GarageDesk',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Icono.ico',
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GarageDesk',
)
