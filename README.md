# Семейное древо

Приложение для построения и редактирования семейного генеалогического дерева.
Desktop-версия (Windows) и веб-версия используют общие данные.

**Версия:** 1.3.0 (Services + Timeline)

[![CI/CD](https://github.com/Andrey1803/family-tree/actions/workflows/ci.yml/badge.svg)](https://github.com/Andrey1803/family-tree/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🆕 Новые возможности (версия 1.3.0)

### 📦 Сервисный слой
- **TreeService** — операции с деревом (загрузка, сохранение, валидация)
- **ExportService** — экспорт в PDF, CSV, текст
- **BackupService** — резервное копирование
- **UndoService** — отмена/повтор действий
- **KinshipService** — вычисление родства
- **ThemeService** — управление темами
- **SettingsService** — настройки пользователя

### 🧪 Тестирование
- Юнит-тесты для сервисов и моделей
- Интеграционные тесты для веб-API
- Покрытие кода (coverage)

### 🔒 Безопасность (web)
- Хеширование паролей через bcrypt
- Генерация SECRET_KEY
- Обратная совместимость

### 📄 Миграции данных
- Автоматическое обновление формата JSON
- Поддержка версий 1.0.0 → 1.3.0

### 🐳 Docker
- Контейнеризация веб-версии
- Gunicorn с workers

### 🚀 CI/CD
- GitHub Actions для автотестов
- Сборка .exe при релизе
- Публикация релизов

---

## 🆕 Версия 1.2.0 (Design Update)

### 🎨 Современный дизайн
- **Градиентные карточки** — плавные переходы цветов
- **Скруглённые углы** — 10px радиус
- **Мягкие тени** — эффект глубины
- **Сглаженные линии** — закруглённые окончания

### 🎯 Улучшенная палитра
- **Светлая тема** — профессиональная, для офиса
- **Тёмная тема** — комфортная, для вечера

---

## 🆕 Версия 1.1.0

### Автосохранение и резервное копирование
- **Автосохранение** каждые 5 минут
- **Резервные копии** до 10 шт.
- **Восстановление** из бэкапа

### Горячие клавиши
| Клавиша | Действие |
|---------|----------|
| `Ctrl+S` | Сохранить данные |
| `Ctrl+Z` | Отменить действие |
| `Ctrl+Y` | Повторить действие |
| `Ctrl+F` | Режим фокуса |
| `Ctrl+T` | Временная шкала |

### Тёмная тема
**Меню → Вид → Тёмная тема**

### Временная шкала (Timeline)
**Меню → Вид → Временная шкала** или `Ctrl+T`

---

## Структура проекта

```
.
├── main.py                    # Точка входа desktop-приложения
├── version.py                 # Версия (1.3.0)
├── requirements.txt           # Зависимости desktop
├── requirements-dev.txt       # Все зависимости (dev)
├── pyproject.toml             # Настройки pytest, coverage
├── build_exe.spec             # Сборка .exe
├── README.md, LICENSE
├── Дерево/                    # Desktop (tkinter)
│   ├── main.py, app.py, auth.py
│   ├── models.py, constants.py, ui_helpers.py
│   ├── services/              # Сервисный слой (новый!)
│   │   ├── __init__.py
│   │   ├── tree_service.py
│   │   ├── export_service.py
│   │   ├── backup_service.py
│   │   ├── undo_service.py
│   │   ├── kinship_service.py
│   │   ├── theme_service.py
│   │   └── settings_service.py
│   ├── data_migrations.py     # Миграции данных (новый!)
│   └── protocol_win.py        # Протокол derevo://
├── web/                       # Веб (Flask)
│   ├── app.py                 # Flask-приложение
│   ├── tree_service.py        # Загрузка/сохранение
│   ├── templates/, static/
│   ├── Dockerfile             # Контейнеризация (новый!)
│   └── requirements.txt
├── tests/                     # Тесты (новый!)
│   ├── test_services.py
│   ├── test_models.py
│   └── test_web.py
├── scripts/                   # Скрипты запуска и сборки
│   └── ...
└── docs/                      # Документация
    ├── STRUCTURE.md
    ├── DATA.md
    ├── API.md                 # API документация (новый!)
    ├── CHANGELOG.md
    └── RELEASE.md
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
| [docs/API.md](docs/API.md) | API документация |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | История изменений |
| [docs/RELEASE.md](docs/RELEASE.md) | Подготовка к релизу |

## Тестирование

```bash
# Запуск тестов
pytest

# Запуск с покрытием
pytest --cov=Дерево --cov=web

# Запуск конкретных тестов
pytest tests/test_services.py
pytest tests/test_models.py
pytest tests/test_web.py
```

## Docker

```bash
# Сборка образа
docker build -f web/Dockerfile -t family-tree-web .

# Запуск контейнера
docker run -p 8000:8000 -v /path/to/data:/data family-tree-web

# Доступ: http://localhost:8000
```
