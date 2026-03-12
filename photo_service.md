# 📸 PHOTO SERVICE - СЕРВИС РАБОТЫ С ФОТО

**Расположение:** `Дерево/services/photo_service.py`

## 🎯 Назначение

Сервис сжимает фотографии и создаёт миниатюры для гибридной системы хранения:
- **Миниатюра** (`photo`): 200×200, ~10-30 KB — для карточек и синхронизации
- **Полное фото** (`photo_full`): 800×800, ~50-150 KB — для просмотра в вебе

## 📦 Зависимости

```bash
pip install Pillow>=9.0.0
```

## 🔧 Использование

### 1. Сжатие фото
```python
from services.photo_service import compress_image

# Сжать до 800x800 с качеством 85%
compressed = compress_image("photo.jpg", max_size=(800, 800), quality=85)
```

### 2. Создание миниатюры
```python
from services.photo_service import create_thumbnail

# Миниатюра 200x200
thumb = create_thumbnail("photo.jpg", size=(200, 200), quality=75)
```

### 3. Конвертация в base64
```python
from services.photo_service import image_to_base64, base64_to_image

# В base64
b64 = image_to_base64(compressed_data)

# Из base64
original = base64_to_image(b64)
```

### 4. Подготовка для синхронизации
```python
from services.photo_service import get_photo_data

# Получить оба формата
data = get_photo_data("photo.jpg", include_full=True)
# data = {
#     'thumbnail': 'base64...',  # 200x200
#     'full': 'base64...'        # 800x800
# }
```

## ⚙️ Настройки

В начале файла:
```python
THUMBNAIL_SIZE = (200, 200)    # Размер миниатюры
PREVIEW_SIZE = (800, 800)      # Размер полного фото
MAX_FILE_SIZE_KB = 100         # Макс. размер миниатюры в KB
```

## 📊 Результаты сжатия

| Оригинал | Миниатюра | Полное | Экономия |
|----------|-----------|--------|----------|
| 1920×1080, 500 KB | 200×200, 15 KB | 800×800, 80 KB | **85%** |
| 4000×3000, 2 MB | 200×200, 20 KB | 800×800, 100 KB | **94%** |

## 🧪 Тестирование

```bash
python test_photo_service.py
```

Все тесты проходят ✅ (6/6)

## 📁 Структура

```
Family tree/
├── Дерево/
│   ├── services/
│   │   └── photo_service.py  ← Этот файл
│   └── app.py                ← Вызывает photo_service
├── web/
│   └── app.py                ← API /api/photo/<id>/full
└── sync_server/
    └── app.py                ← БД с photo_full
```

## 🔍 Примеры использования

### В desktop-версии (app.py)
```python
from services.photo_service import get_photo_data

photo_path = "photos/user/1.jpg"
photo_data = get_photo_data(photo_path, include_full=True)

person.photo = photo_data['thumbnail']      # Для сервера
person.photo_full = photo_data['full']      # Для веба
```

### В веб-версии (app.py)
```python
# Миниатюра для карточки
GET /api/photo/1
# Возвращает image/jpeg (миниатюра из photo)

# Полное фото для просмотра
GET /api/photo/1/full
# Возвращает image/jpeg (из photo_full)
```

## 🐛 Устранение проблем

### "PIL не доступен"
```bash
pip install Pillow
```

### "Файл не найден"
Проверьте путь:
```python
import os
print(os.path.exists(photo_path))  # Должно быть True
```

### "Слишком большой размер"
Уменьшите качество или размер:
```python
compress_image(path, max_size=(600, 600), quality=60)
```

---

**Версия:** 1.0  
**Дата:** 12.03.2026
