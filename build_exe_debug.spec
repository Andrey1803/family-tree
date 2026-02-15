# -*- mode: python ; coding: utf-8 -*-
# Сборка с консолью (для отладки): pyinstaller build_exe_debug.spec
# Ошибки будут видны в окне консоли

from pathlib import Path

_block_cipher = None
root = Path(SPECPATH)
tree_dir = root / 'Дерево'

a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root), str(tree_dir)],
    binaries=[],
    datas=[(str(tree_dir), 'Дерево')] if tree_dir.is_dir() else [],
    hiddenimports=[
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
    name='Семейное_древо_DEBUG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
