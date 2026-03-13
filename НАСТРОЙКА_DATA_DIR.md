# 🚀 НАСТРОЙКА DATA_DIR НА RAILWAY

## ❌ ТЕКУЩАЯ ПРОБЛЕМА

В Railway Dashboard переменная установлена неправильно:
```
DATA_DIR = /app/data  ❌
```

Это **временная папка** — она очищается при каждом деплое!

---

## ✅ КАК ИСПРАВИТЬ

### Шаг 1: Изменить переменную DATA_DIR

1. Откройте Railway Dashboard: https://railway.app/
2. Проект `family-tree-production` → сервис `family-tree`
3. Вкладка **Variables**
4. Найдите `DATA_DIR`
5. Измените значение:
   ```
   DATA_DIR = /data  ✅
   ```
6. Нажмите **Save**

### Шаг 2: Создать Volume (постоянное хранилище)

1. В том же сервисе `family-tree`
2. Перейдите на вкладку **Volumes**
3. Нажмите **"+ New Volume"**
4. Настройте:
   - **Mount Path:** `/data`
   - **Size:** 1 GB (минимум)
5. Нажмите **"Create Volume"**

### Шаг 3: Перезапустить сервис

1. Вкладка **Deployments**
2. Нажмите **"Restart"** (или "Redeploy")
3. Дождитесь завершения (1-2 минуты)

---

## 🧪 ПРОВЕРКА

### 1. Проверьте логи

В Railway Dashboard → **Deployments** → **View Logs**:

Должны появиться:
```
[CONFIG] Using DATA_DIR from env: /data
[CONFIG] USERS_FILE=/data/users.json
[TREE_SERVICE] Loaded X persons for username
```

### 2. Проверьте через консоль

Railway Dashboard → **Deployments** → **Console**:

```bash
# Проверить что Volume подключён
ls -la /data/

# Должны быть файлы после создания дерева:
# users.json
# family_tree_*.json
# palette.json
```

### 3. Протестируйте сохранение

1. Откройте веб-приложение
2. Зарегистрируйте нового пользователя
3. Создайте дерево
4. Перезапустите сервис на Railway
5. Войдите снова — дерево должно сохраниться!

---

## 📊 ЧТО ИЗМЕНИТСЯ

| До | После |
|----|-------|
| `DATA_DIR=/app/data` | `DATA_DIR=/data` ✅ |
| Данные теряются при деплое | Данные сохраняются навсегда ✅ |
| Volume не подключён | Volume 1GB подключён ✅ |

---

## ⚠️ ВАЖНО

**После изменения DATA_DIR:**
- Старые данные из `/app/data` не перенесутся автоматически
- Пользователям придётся зарегистрироваться заново
- Это одноразовая настройка — больше не потребуется

---

## 🔗 ССЫЛКИ

- [Railway Volumes](https://docs.railway.app/storage/volumes)
- [Railway Variables](https://docs.railway.app/develop/variables)

---

**Обновлено:** 13 марта 2026 г.
