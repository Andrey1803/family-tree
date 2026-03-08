# Семейное древо

Приложение для построения и редактирования семейного генеалогического дерева.  
Desktop-версия (Windows) и веб-версия используют общие данные.

**Версия:** 1.0.0

---

## Структура проекта

```
.
├── main.py              # Точка входа desktop-приложения
├── version.py           # Версия
├── requirements.txt     # Pillow (desktop)
├── requirements-dev.txt # Все зависимости
├── build_exe.spec       # Сборка .exe
├── README.md, LICENSE
├── Дерево/              # Desktop (tkinter)
│   ├── main.py, app.py, auth.py
│   ├── models.py, constants.py, ui_helpers.py
│   └── protocol_win.py  # Протокол derevo://
├── web/                 # Веб (Flask)
│   ├── app.py, tree_service.py
│   ├── templates/, static/
│   └── requirements.txt
├── scripts/             # run_desktop.bat, run_web.bat, build_exe.bat, ...
└── docs/                # STRUCTURE.md, DATA.md, CHANGELOG.md, RELEASE.md
```

Подробнее: [docs/STRUCTURE.md](docs/STRUCTURE.md)

**Файлы данных** (создаются при первом запуске в корне проекта):  
`users.json`, `family_tree_*.json`, `user_settings_*.json`, `palette.json`, `window_settings.json`

---

## Быстрый старт

### Desktop (Windows)

```bash
pip install -r requirements.txt
python main.py
```

Или: `scripts\run_desktop.bat`

### Веб

```bash
cd web
pip install -r requirements.txt
python app.py
```

Открыть: http://127.0.0.1:5000  

Или: `scripts\run_web.bat`

### Полная установка (desktop + web + сборка)

```bash
pip install -r requirements-dev.txt
```

---

## Сборка .exe (Windows)

```bash
pip install pyinstaller pillow
pyinstaller build_exe.spec
```

Готовый файл: `dist/Семейное_древо.exe`  

Или: `scripts\build_exe.bat`

При первом запуске exe создаст файлы данных в той же папке.

---

## Развёртывание в интернет (Railway)

См. [docs/RAILWAY.md](docs/RAILWAY.md) — деплой на [railway.com](https://railway.com) для глобального доступа.

---

## Документация

| Файл | Описание |
|------|----------|
| [web/README.md](web/README.md) | Веб-интерфейс, детали |
| [docs/STRUCTURE.md](docs/STRUCTURE.md) | Структура проекта |
| [docs/DATA.md](docs/DATA.md) | Файлы данных |
| [docs/RAILWAY.md](docs/RAILWAY.md) | Деплой на Railway |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | История изменений |
| [docs/RELEASE.md](docs/RELEASE.md) | Подготовка к релизу |
