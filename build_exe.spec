# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller build_exe.spec
# Требуется: pip install pyinstaller pillow

from pathlib import Path

_block_cipher = None

# Корень проекта
root = Path(SPECPATH)
tree_dir = root / 'Дерево'

# Данные для приложения (Tcl/Tk — через стандартный hook PyInstaller)
datas_list = [(str(tree_dir), 'Дерево')] if tree_dir.is_dir() else []

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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Семейное_древо',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # без консоли — выглядит как обычное приложение
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
)
