# 🚀 Развёртывание на Railway

## 📋 Структура sync_server

```
sync_server/
├── app.py              # Flask приложение
├── create_tables.py    # Скрипт создания таблиц
├── prestart.sh         # Pre-start скрипт для Railway
├── requirements.txt    # Зависимости
├── railway.json        # Конфигурация Railway
└── wsgi.py            # WSGI entry point
```

## 🔧 Развёртывание

### 1. Подготовка

```bash
# Убедитесь что все файлы в sync_server/ актуальны
cd sync_server
git status
```

### 2. Деплой на Railway

1. Откройте https://railway.app
2. Создайте новый проект
3. Выберите "Deploy from GitHub repo"
4. Выберите репозиторий `family-tree`
5. В настройках укажите Root Directory: `sync_server`

### 3. Настройка переменных окружения

В Railway Dashboard добавьте переменные:

```
SECRET_KEY=your-secret-key-here
DATA_DIR=/data
FLASK_DEBUG=False
```

### 4. Добавление Volume

1. В проекте нажмите "+ New" → "Volume"
2. Назовите: `data`
3. Mount Path: `/data`

### 5. Проверка

После деплоя проверьте:

```bash
# Проверка статистики
curl https://your-app.railway.app/api/admin/stats

# Проверка пользователей
curl https://your-app.railway.app/api/admin/users
```

## 🔍 Диагностика

### Логи Railway

Откройте Railway Dashboard → Logs

### Проблемы с БД

Если БД не создаётся:

```bash
# Локально проверьте prestart.sh
bash prestart.sh

# Проверьте что таблицы создались
python -c "import sqlite3; conn=sqlite3.connect('/data/family_tree.db'); cur=conn.cursor(); cur.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); print(cur.fetchall())"
```

## 📝 Примечания

- **Volume обязателен** — без него данные будут теряться при перезапуске
- **prestart.sh** выполняется перед запуском Gunicorn
- **SECRET_KEY** должен быть уникальным для production
