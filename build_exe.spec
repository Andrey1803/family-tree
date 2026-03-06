# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller build_exe.spec
# Требуется: pip install pyinstaller pillow

from pathlib import Path
import os

_block_cipher = None

# Корень проекта
root = Path(SPECPATH)
tree_dir = root / 'Дерево'
data_dir = root / 'data'

# Данные для приложения
datas_list = [(str(tree_dir), 'Дерево')] if tree_dir.is_dir() else []
# Добавляем папку data в сборку
if data_dir.is_dir():
    datas_list.append((str(data_dir), 'data'))

a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root), str(tree_dir)],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        # Кодировки
        'encodings', 'encodings.utf_8', 'encodings.cp1251', 'encodings.cp1252',
        'encodings.latin_1', 'encodings.ascii', 'encodings.cp866',
        # PIL
        'PIL', 'PIL._tkinter_finder', 'PIL.Image', 'PIL.ImageTk', 'PIL.PngImagePlugin',
        'PIL.JpegImagePlugin', 'PIL.GifImagePlugin', 'PIL.BmpImagePlugin',
        # Модули Дерево
        'app', 'auth', 'models', 'constants', 'ui_helpers', 'protocol_win',
        'version', 'update_check', 'backup', 'undo', 'kinship', 'theme',
        'timeline', 'sync', 'check_parents', 'data_migrations',
        'user_dashboard', 'server_admin_dashboard', 'admin_dashboard_full',
        'admin_dashboard_local',
        # Сервисы
        'services',
        'services.tree_service',
        'services.export_service',
        'services.backup_service',
        'services.undo_service',
        'services.kinship_service',
        'services.theme_service',
        'services.settings_service',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas', 'pygame',
        'tkinter.test',
        'reportlab',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=_block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=_block_cipher)

# EXE с данными
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
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
