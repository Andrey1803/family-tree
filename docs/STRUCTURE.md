# Структура проекта «Семейное древо»

## Дерево каталогов

```
.
├── main.py                 # Точка входа desktop-приложения
├── version.py              # Версия (1.0.0)
├── requirements.txt        # Pillow (desktop)
├── requirements-dev.txt    # Все зависимости (desktop + web + PyInstaller)
├── build_exe.spec          # Сборка .exe (PyInstaller)
├── README.md               # Документация
├── LICENSE                 # Лицензия
│
├── Дерево/                 # Desktop-версия (tkinter)
│   ├── main.py             # Логика запуска, авторизация
│   ├── app.py              # Главное окно, холст, меню, диалоги
│   ├── auth.py             # Окно входа
│   ├── models.py           # Person, FamilyTreeModel
│   ├── constants.py        # Константы, палитра
│   ├── ui_helpers.py       # Вспомогательные виджеты
│   └── protocol_win.py     # Регистрация протокола derevo://
│
├── web/                    # Веб-версия (Flask)
│   ├── app.py              # Flask-приложение, API, авторизация
│   ├── tree_service.py     # Загрузка/сохранение дерева
│   ├── requirements.txt    # Flask, Werkzeug
│   ├── README.md           # Инструкции по веб-версии
│   ├── templates/          # HTML-шаблоны
│   │   ├── login.html
│   │   ├── register.html
│   │   └── tree.html
│   └── static/
│       ├── css/style.css
│       ├── js/tree.js
│       ├── sw.js            # Service Worker (PWA)
│       ├── manifest.json
│       └── icon.svg
│
├── scripts/                # Скрипты запуска и сборки (Windows)
│   ├── run_desktop.bat     # Запуск desktop
│   ├── run_web.bat         # Запуск веб-сервера
│   ├── build_exe.bat       # Сборка .exe
│   ├── prepare_release.bat # Подготовка к релизу (сборка exe)
│   ├── create_release_zip.bat # ZIP с исходниками
│   └── create_release_zip.py  # (вызывается из .bat)
│
└── docs/
    ├── STRUCTURE.md        # Этот файл
    ├── DATA.md             # Файлы данных
    ├── CHANGELOG.md        # История изменений
    └── RELEASE.md          # Инструкции по релизу
```

## Файлы данных (создаются при первом запуске)

Хранятся в **корне проекта** (рядом с `main.py`):

| Файл | Описание |
|------|----------|
| `users.json` | Учётные записи (логин, хеш пароля) |
| `family_tree_Имя.json` | Дерево пользователя «Имя» |
| `family_tree_Гость.json` | Дерево для гостя |
| `user_settings_*.json` | Настройки пользователя |
| `login_remember.json` | Запомненный логин (desktop) |
| `palette.json` | Цветовая палитра |
| `window_settings.json` | Размер и позиция окна (desktop) |

Эти файлы **не включены в репозиторий** (см. `.gitignore`).  
Подробнее: [docs/DATA.md](DATA.md)

## Исключённые из репозитория (см. .gitignore)

| Категория | Паттерн | Описание |
|-----------|---------|----------|
| Сборка | `dist/`, `build/` | Папки PyInstaller |
| Релиз | `Семейное_древо_*_source.zip` | Архивы исходников |
| Данные | `users.json`, `family_tree*.json`, … | Файлы пользователя |
| IDE | `.idea/`, `.vscode/` | Настройки IDE |

## Общие данные

Desktop и web используют одни и те же файлы. Дерево, созданное в одной версии, отображается в другой.
