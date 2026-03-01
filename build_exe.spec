# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller build_exe.spec
# Требуется: pip install pyinstaller pillow

from pathlib import Path

_block_cipher = None

# Корень проекта
root = Path(SPECPATH)
tree_dir = root / 'Дерево'
services_dir = tree_dir / 'services'

# Данные для приложения + Tcl/Tk
datas_list = [(str(tree_dir), 'Дерево')] if tree_dir.is_dir() else []
try:
    from PyInstaller.utils.hooks.tcl_tk import tcltk_info
    if tcltk_info.data_files:
        for dest, src, kind in tcltk_info.data_files:
            s, d = str(src), str(dest)
            # Исключаем ненужные файлы локализации
            skip = any(x in d or x in s for x in ('tzdata', 'msgs', 'macRoman', 'macCyrillic', 'macUkraine', 'macIceland', 'macTurkish', 'macDingbats'))
            if not skip:
                datas_list.append((src, dest))
except Exception as e:
    print(f"Warning: Could not get Tcl/Tk info: {e}")

a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root), str(tree_dir)],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        # Кодировки
        'encodings', 'encodings.utf_8', 'encodings.cp1251', 'encodings.cp1252',
        'encodings.latin_1', 'encodings.ascii',
        # PIL
        'PIL', 'PIL._tkinter_finder', 'PIL.Image', 'PIL.ImageTk', 'PIL.PngImagePlugin',
        'PIL.JpegImagePlugin', 'PIL.GifImagePlugin',
        # Модули Дерево
        'app', 'auth', 'models', 'constants', 'ui_helpers', 'protocol_win',
        'version', 'update_check', 'backup', 'undo', 'kinship', 'theme',
        'timeline', 'sync', 'check_parents', 'data_migrations',
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
        'matplotlib', 'numpy', 'scipy', 'pandas', 'pygame',  # Не используются
        'tkinter.test',  # Тесты tkinter
        'reportlab',  # Нет в requirements
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=_block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=_block_cipher)

# onedir — Tcl/Tk стабильно работает на других ПК
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