# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller build_exe.spec
# Требуется: pip install pyinstaller pillow

from pathlib import Path

_block_cipher = None

# Корень проекта
root = Path(SPECPATH)
tree_dir = root / 'Дерево'

# Данные для приложения + Tcl/Tk (обязательно для tkinter на другом ПК)
datas_list = [(str(tree_dir), 'Дерево')] if tree_dir.is_dir() else []
try:
    from PyInstaller.utils.hooks.tcl_tk import tcltk_info
    if tcltk_info.data_files:
        datas_list.extend((src, dest) for dest, src, _ in tcltk_info.data_files)
except Exception:
    pass

a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root), str(tree_dir)],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'encodings', 'encodings.utf_8', 'encodings.cp1251',
        'PIL', 'PIL._tkinter_finder',
        'app', 'auth', 'models', 'constants', 'ui_helpers', 'protocol_win',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=_block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=_block_cipher)

# onedir — Tcl/Tk стабильно работает на других ПК (onefile даёт init.tcl error)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Семейное_древо',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Семейное_древо',
)