# 🚀 ВОССТАНОВЛЕНИЕ СЕРВИСА RAVISHING-CARING

## 📋 Что было исправлено

### 1. **Procfile** — убран блокирующий скрипт
**Было:**
```
web: python fix_admin_once.py && gunicorn app:app -b 0.0.0.0:$PORT
```

**Стало:**
```
web: gunicorn app:app -b 0.0.0.0:$PORT
```

**Причина:** Если `fix_admin_once.py` падал с ошибкой, сервер не запускался.

---

### 2. **railway.toml** — добавлен prestart
**Было:**
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "gunicorn app:app -b 0.0.0.0:$PORT"
```

**Стало:**
```toml
[build]
builder = "NIXPACKS"
prestart = "bash prestart.sh"

[deploy]
startCommand = "gunicorn app:app -b 0.0.0.0:$PORT"
```

**Причина:** Явное указание скрипта prestart для миграций.

---

### 3. **prestart.sh** — добавлена миграция photo_full
Теперь при старте автоматически добавляется колонка `photo_full` если её нет.

---

### 4. **requirements.txt** — добавлен Pillow
**Было:**
```txt
Flask==3.0.0
Flask-CORS==4.0.0
bcrypt==4.1.2
gunicorn==21.2.0
psycopg2-binary==2.9.9
```

**Стало:**
```txt
Flask==3.0.0
Flask-CORS==4.0.0
bcrypt==4.1.2
gunicorn==21.2.0
psycopg2-binary==2.9.9
Pillow>=9.0.0
```

**Причина:** Требуется для обработки фото.

---

### 5. **app.py** — исправлен путь к БД по умолчанию
**Было:**
```python
DB_FILE = os.environ.get('DATA_DIR', '.') + '/family_tree.db'
```

**Стало:**
```python
DB_FILE = os.environ.get('DATA_DIR', '/data') + '/family_tree.db'
```

**Причина:** Путь `/data` — стандарт для Railway volume.

---

## 🔧 ИНСТРУКЦИЯ ПО ДЕПЛОЮ

### Шаг 1: Закоммитьте изменения

```powershell
# PowerShell (для обхода проблем с кодировкой)
chcp 65001
cd "d:\Мои документы\Рабочий стол\hobby\Projects\Family tree"

git add sync_server/Procfile
git add sync_server/railway.toml
git add sync_server/prestart.sh
git add sync_server/requirements.txt
git add sync_server/app.py

git commit -m "fix: восстановить сервис ravishing-caring"
git push origin main
```

**Или одной командой:**
```powershell
powershell chcp 65001; cd 'd:\Мои документы\Рабочий стол\hobby\Projects\Family tree'; git add sync_server/Procfile sync_server/railway.toml sync_server/prestart.sh sync_server/requirements.txt sync_server/app.py; git commit -m "fix: восстановить сервис ravishing-caring"; git push origin main
```

---

### Шаг 2: Проверьте переменные окружения на Railway

Откройте **Railway Dashboard** → Проект `family-tree-production` → Сервис `ravishing-caring`:

**Обязательные переменные:**
```bash
SECRET_KEY=ваш_секретный_ключ_32_символа
DATA_DIR=/data
PORT=5000
```

**Опциональные:**
```bash
FLASK_DEBUG=false
ANDREY_SUPER_ADMIN=true
```

---

### Шаг 3: Дождитесь деплоя

1. Откройте **Deployments** в Railway Dashboard
2. Дождитесь завершения сборки (2-5 минут)
3. Проверьте логи на наличие ошибок

**Ожидаемые логи:**
```
🔧 Railway Pre-start
📦 DATA_DIR env: /data
📦 DB_FILE: /data/family_tree.db
✅ БД существует. Пользователей: X
🔧 Проверка миграции photo_full...
✅ photo_full уже существует
✅ Pre-start завершён!
🚀 Запуск Gunicorn...
[DB] DB_DIR: /data
[DB] Database already initialized. Users: X
🚀 Запуск сервера на порту 5000...
```

---

### Шаг 4: Проверьте доступность сервиса

**Вариант 1: Через браузер**
```
https://ravishing-caring-production-3656.up.railway.app
```

**Вариант 2: Через API**
```bash
curl https://ravishing-caring-production-3656.up.railway.app/api/health
```

**Ожидаемый ответ:**
```json
{
  "status": "ok",
  "timestamp": "2026-03-12T...",
  "database": {
    "status": "connected",
    "path": "/data"
  },
  "version": "1.0.0"
}
```

---

### Шаг 5: Проверьте базу данных

**Через консоль Railway:**
```bash
# Откройте Console в Railway Dashboard
sqlite3 /data/family_tree.db

# Проверка структуры
PRAGMA table_info(persons);

# Проверка пользователей
SELECT id, login, is_admin FROM users;

# Выход
.exit
```

**Ожидаемый результат:**
- Колонка `photo_full BLOB` присутствует
- Пользователь `Андрей Емельянов` имеет `is_admin = 1`

---

## 🐛 УСТРАНЕНИЕ ПРОБЛЕМ

### Ошибка: "no such table: users"

**Причина:** База данных не инициализирована

**Решение:**
```bash
# В консоли Railway
cd /app
python -c "from sync_server.app import init_db; init_db()"
```

---

### Ошибка: "unable to open database file"

**Причина:** Нет прав на запись в `/data`

**Решение:**
1. Проверьте переменную `DATA_DIR=/data`
2. В Railway Dashboard → Settings → Volumes → Добавьте volume `/data`

---

### Ошибка: "PIL not available"

**Причина:** Не установлен Pillow

**Решение:**
1. Проверьте `sync_server/requirements.txt` (должен быть `Pillow>=9.0.0`)
2. Перезапустите деплой

---

### Сервис запускается и сразу падает

**Проверьте логи:**
```bash
# В Railway Dashboard откройте Logs
# Ищите строки с [DB] Error или Exception
```

**Возможные причины:**
- Нет переменной `SECRET_KEY`
- Порт не совпадает с `PORT` в переменных
- Конфликт миграций

---

## ✅ ЧЕКЛИСТ ПРОВЕРКИ

- [ ] Изменения закоммичены и запушены
- [ ] Переменные окружения установлены на Railway
- [ ] Volume `/data` подключён
- [ ] Деплой прошёл без ошибок
- [ ] `/api/health` возвращает `status: ok`
- [ ] База данных содержит таблицу `persons` с `photo_full`
- [ ] Пользователь `Андрей Емельянов` имеет права админа
- [ ] Веб-приложение подключается к серверу

---

## 📊 МОНИТОРИНГ

### Проверка логов в реальном времени

1. Railway Dashboard → Сервис → **Logs**
2. Фильтр по уровню: `ERROR`, `WARNING`

### Проверка использования места

```sql
-- Размер базы данных
SELECT page_count * page_size as db_size_bytes 
FROM pragma_page_count(), pragma_page_size();

-- Размер всех фото
SELECT 
    SUM(length(photo)) / 1024 as thumbnails_kb,
    SUM(length(photo_full)) / 1024 as full_photos_kb
FROM persons
WHERE photo IS NOT NULL;
```

---

## 🎯 ИТОГ

После восстановления:
- ✅ Сервер синхронизации работает
- ✅ Веб-версия и desktop синхронизируются
- ✅ Админ-панель доступна Андрею Емельянову
- ✅ Фото загружаются и хранятся корректно

**Готово!** 🎉

---

## 📞 ПОДДЕРЖКА

Если что-то пошло не так:

1. Проверьте логи в Railway Dashboard
2. Выполните тестовый запрос к `/api/health`
3. Проверьте переменные окружения
4. Убедитесь что volume `/data` подключён
