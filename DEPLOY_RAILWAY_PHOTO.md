# 🚀 РАЗВЁРТЫВАНИЕ НА RAILWAY: ОБНОВЛЕНИЕ С PHOTO_FULL

## 📋 Обзор изменений

Добавлено новое поле `photo_full` для хранения полных версий фото в гибридной системе:
- **Миниатюра** (`photo`): 200×200, ~10-30 KB — для карточек
- **Полное фото** (`photo_full`): 800×800, ~50-150 KB — для просмотра

---

## 🔧 ШАГ 1: Подготовка базы данных

### Вариант A: Новая база данных (автоматически)

Если развёртываете **с нуля** — ничего делать не нужно. Поле `photo_full` уже есть в схеме:

```sql
CREATE TABLE IF NOT EXISTS persons (
    ...
    photo BLOB,
    photo_full BLOB,  -- ← Уже есть в схеме
    ...
)
```

### Вариант B: Существующая база данных (миграция)

Если база **уже существует**, выполните миграцию:

#### 1. Локально (для тестирования)
```bash
cd sync_server
python migrate_add_photo_full.py
```

#### 2. На Railway (через Deploy)

**Способ 1: Через консоль Railway**
```bash
# Откройте консоль в Railway Dashboard
cd /app
python sync_server/migrate_add_photo_full.py
```

**Способ 2: Автоматически при старте**

Добавьте в `app.py` перед `init_db()`:

```python
def migrate_add_photo_full_if_needed():
    """Добавляет поле photo_full если отсутствует."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(persons)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'photo_full' not in columns:
        print("[MIGRATION] Adding photo_full column...")
        cursor.execute('ALTER TABLE persons ADD COLUMN photo_full BLOB')
        print("[MIGRATION] Done!")
    else:
        print("[MIGRATION] photo_full already exists")
    
    conn.commit()
    conn.close()

# Вызвать ПЕРЕД init_db()
migrate_add_photo_full_if_needed()
init_db()
```

---

## 📦 ШАГ 2: Обновление зависимостей

### Проверьте `requirements.txt`

Убедитесь, что есть **Pillow** для обработки фото:

```txt
Flask==3.0.0
Flask-CORS==4.0.0
bcrypt==4.1.2
gunicorn==21.2.0
psycopg2-binary==2.9.9
Pillow>=9.0.0  # ← Обязательно!
```

### Обновите зависимости на Railway

В Railway Dashboard → Variables → Добавьте:
```
NIXPACKS_PYTHON_VERSION=3.11
```

Или обновите `nixpacks.toml`:

```toml
[phases.setup]
nixPkgs = ["python311"]

[phases.install]
cmds = ["pip install -r requirements.txt"]
```

---

## 🔄 ШАГ 3: Деплой обновлённой версии

### 1. Закоммитьте изменения
```bash
git add sync_server/app.py
git add sync_server/migrate_add_photo_full.py
git add web/app.py
git add Дерево/services/photo_service.py
git add Дерево/models.py
git add Дерево/app.py
git commit -m "Add photo_full field for hybrid photo storage"
git push origin main
```

### 2. Railway автоматически обновится

Проверьте логи в Railway Dashboard:
```
[PHOTO] Миниатюра: 1200 символов, Полное: 4800 символов
[MIGRATION] photo_full already exists
```

---

## ⚙️ ШАГ 4: Настройка переменных окружения

В Railway Dashboard → Variables установите:

```bash
# Обязательно
SECRET_KEY=ваш_секретный_ключ_32_символа
DATA_DIR=/data  # Для volume-хранилища

# Опционально
ANDREY_SUPER_ADMIN=true  # Права Андрея
REMOVE_ADMIN=false       # Удалить admin по умолчанию
```

---

## 🧪 ШАГ 5: Тестирование

### 1. Проверка API

```bash
# Проверка миниатюры
curl https://your-railway-app.up.railway.app/api/photo/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output thumbnail.jpg

# Проверка полного фото
curl https://your-railway-app.up.railway.app/api/photo/1/full \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output full.jpg
```

### 2. Проверка базы данных

```bash
# Подключитесь к консоли Railway
sqlite3 /data/family_tree.db

# Проверьте структуру
PRAGMA table_info(persons);

# Проверьте данные
SELECT id, name, surname, 
       length(photo) as photo_size, 
       length(photo_full) as full_size 
FROM persons 
WHERE photo IS NOT NULL 
LIMIT 5;
```

Ожидаемый результат:
```
id|name|surname|photo_size|full_size
1|Андрей|Емельянов|1200|4800
```

---

## 📊 МОНИТОРИНГ

### Проверка использования места

```sql
-- Размер всех фото в БД
SELECT 
    SUM(length(photo)) / 1024 / 1024 as thumbnails_mb,
    SUM(length(photo_full)) / 1024 / 1024 as full_photos_mb,
    SUM(length(photo) + length(photo_full)) / 1024 / 1024 as total_mb
FROM persons;
```

### Логирование

Добавьте в `app.py` для отладки:

```python
@app.after_request
def log_photo_usage(response):
    if request.endpoint == 'api_photo_full':
        person_id = request.view_args['person_id']
        app.logger.info(f"Photo full requested: {person_id}")
    return response
```

---

## 🐛 УСТРАНЕНИЕ ПРОБЛЕМ

### Ошибка: "no such column: photo_full"

**Решение:**
```bash
# Выполните миграцию
python sync_server/migrate_add_photo_full.py

# Или вручную в SQLite
sqlite3 /data/family_tree.db
ALTER TABLE persons ADD COLUMN photo_full BLOB;
```

### Ошибка: "PIL not available"

**Решение:**
```bash
# Обновите requirements.txt
echo "Pillow>=9.0.0" >> requirements.txt

# Перезапустите pod в Railway
# Railway Dashboard → Settings → Restart
```

### Фото не отображается в вебе

**Проверка:**
1. Откройте консоль браузера (F12)
2. Проверьте запросы к `/api/photo/*/full`
3. Проверьте ответ сервера (должен быть 200 OK)

**Решение:**
```bash
# Проверьте, что фото есть в БД
sqlite3 /data/family_tree.db
SELECT id, photo_full IS NOT NULL as has_full FROM persons WHERE id='1';
```

---

## 📈 ОПТИМИЗАЦИЯ

### Сжатие фото

Измените в `Дерево/services/photo_service.py`:

```python
THUMBNAIL_SIZE = (150, 150)  # Меньше = меньше трафик
PREVIEW_SIZE = (600, 600)    # Меньше = быстрее загрузка
MAX_FILE_SIZE_KB = 50        # Строгий лимит
quality=70                   # Ниже качество, меньше размер
```

### Кэширование

Добавьте в `web/app.py`:

```python
@app.route("/api/photo/<person_id>/full")
def api_photo_full(person_id):
    # ... код ...
    response = Response(raw, mimetype=mt)
    response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 год
    return response
```

---

## ✅ ЧЕКЛИСТ ДЕПЛОЯ

- [ ] `requirements.txt` обновлён (есть Pillow)
- [ ] Миграция выполнена (`photo_full` в БД)
- [ ] Переменные окружения установлены
- [ ] Деплой прошёл без ошибок
- [ ] API `/api/photo/<id>/full` возвращает 200
- [ ] Миниатюры отображаются в карточках
- [ ] Полные фото открываются по клику
- [ ] Логи показывают загрузку фото

---

## 📞 ПОДДЕРЖКА

Если что-то пошло не так:

1. Проверьте логи в Railway Dashboard
2. Выполните тестовый запрос к API
3. Проверьте БД через SQLite консоль

---

## 🎯 ИТОГ

После развёртывания:
- ✅ Миниатюры (~30 KB) загружаются быстро
- ✅ Полные фото (~100 KB) открываются по запросу
- ✅ Экономия трафика: **70-80%**
- ✅ Место на Railway: **~5 MB** на 42 персоны

**Готово!** 🎉
