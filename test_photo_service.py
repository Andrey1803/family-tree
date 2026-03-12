# -*- coding: utf-8 -*-
"""
Тестирование системы работы с фото.

Проверяет:
1. Сжатие изображений
2. Создание миниатюр
3. Конвертацию в base64
4. Сохранение и загрузку photo_full

Запуск:
    python test_photo_service.py
"""

import os
import sys

# Добавляем путь к сервису
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "Дерево"))

from services.photo_service import (
    compress_image,
    create_thumbnail,
    image_to_base64,
    base64_to_image,
    get_photo_data,
    save_photo_for_sync,
    THUMBNAIL_SIZE,
    PREVIEW_SIZE,
    MAX_FILE_SIZE_KB
)


def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_compress_image():
    """Тест сжатия изображения."""
    print_section("ТЕСТ 1: Сжатие изображения")
    
    # Создаём тестовое изображение
    try:
        from PIL import Image
        test_img = Image.new('RGB', (1920, 1080), color='red')
        test_path = os.path.join(BASE_DIR, "test_image.jpg")
        test_img.save(test_path, quality=95)
        original_size = os.path.getsize(test_path)
        print(f"✓ Создано тестовое изображение: 1920x1080")
        print(f"  Размер оригинала: {original_size // 1024} KB")
    except Exception as e:
        print(f"✗ Ошибка создания тестового изображения: {e}")
        return False
    
    # Сжимаем
    compressed = compress_image(test_path, max_size=PREVIEW_SIZE, quality=85)
    if compressed:
        print(f"✓ Сжатое изображение: {len(compressed) // 1024} KB")
        print(f"  Экономия: {100 - (len(compressed) * 100 // original_size):.0f}%")
    else:
        print(f"✗ Ошибка сжатия")
        os.remove(test_path)
        return False
    
    # Очищаем
    os.remove(test_path)
    print(f"✓ Тест завершён")
    return True


def test_thumbnail():
    """Тест создания миниатюры."""
    print_section("ТЕСТ 2: Создание миниатюры")
    
    try:
        from PIL import Image
        test_img = Image.new('RGB', (1920, 1080), color='blue')
        test_path = os.path.join(BASE_DIR, "test_thumbnail.jpg")
        test_img.save(test_path)
        print(f"✓ Создано изображение: 1920x1080")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False
    
    # Создаём миниатюру
    thumb = create_thumbnail(test_path, size=THUMBNAIL_SIZE, quality=75)
    if thumb:
        print(f"✓ Миниатюра: {len(thumb) // 1024} KB")
        if len(thumb) < MAX_FILE_SIZE_KB * 1024:
            print(f"  ✓ Размер в пределах лимита ({MAX_FILE_SIZE_KB} KB)")
        else:
            print(f"  ✗ Размер превышает лимит!")
    else:
        print(f"✗ Ошибка создания миниатюры")
        os.remove(test_path)
        return False
    
    os.remove(test_path)
    return True


def test_base64():
    """Тест конвертации base64."""
    print_section("ТЕСТ 3: Конвертация base64")
    
    # Создаём тестовые данные
    test_data = b"test image data" * 100
    
    # В base64
    b64 = image_to_base64(test_data)
    if b64:
        print(f"✓ Base64: {len(b64)} символов")
    else:
        print(f"✗ Ошибка кодирования")
        return False
    
    # Из base64
    decoded = base64_to_image(b64)
    if decoded == test_data:
        print(f"✓ Декодирование успешно")
    else:
        print(f"✗ Ошибка декодирования")
        return False
    
    return True


def test_get_photo_data():
    """Тест получения полных данных фото."""
    print_section("ТЕСТ 4: Получение данных фото (thumbnail + full)")
    
    try:
        from PIL import Image
        test_img = Image.new('RGB', (1920, 1080), color='green')
        test_path = os.path.join(BASE_DIR, "test_photo_data.jpg")
        test_img.save(test_path)
        print(f"✓ Создано изображение: 1920x1080")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False
    
    # Получаем данные
    data = get_photo_data(test_path, include_full=True)
    
    if 'thumbnail' in data:
        print(f"✓ Миниатюра: {len(data['thumbnail'])} символов base64")
    else:
        print(f"✗ Миниатюра отсутствует")
        os.remove(test_path)
        return False
    
    if 'full' in data:
        print(f"✓ Полное фото: {len(data['full'])} символов base64")
    else:
        print(f"✗ Полное фото отсутствует")
        os.remove(test_path)
        return False
    
    # Проверяем размеры
    thumb_size = len(data['thumbnail']) * 3 // 4  # base64 -> bytes
    full_size = len(data['full']) * 3 // 4
    
    print(f"\n  Размеры:")
    print(f"    Миниатюра: ~{thumb_size // 1024} KB")
    print(f"    Полное: ~{full_size // 1024} KB")
    
    os.remove(test_path)
    return True


def test_save_photo_for_sync():
    """Тест подготовки фото для синхронизации."""
    print_section("ТЕСТ 5: Подготовка для синхронизации")
    
    try:
        from PIL import Image
        test_img = Image.new('RGB', (1920, 1080), color='yellow')
        test_path = os.path.join(BASE_DIR, "test_sync.jpg")
        test_img.save(test_path)
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False
    
    # Сохраняем для синхронизации
    b64 = save_photo_for_sync(test_path)
    
    if b64:
        size_kb = len(b64) * 3 // 4 // 1024
        print(f"✓ Готово к синхронизации: {size_kb} KB")
        if size_kb <= MAX_FILE_SIZE_KB:
            print(f"  ✓ В пределах лимита")
        else:
            print(f"  ✗ Превышен лимит!")
    else:
        print(f"✗ Ошибка подготовки")
        os.remove(test_path)
        return False
    
    os.remove(test_path)
    return True


def test_model_integration():
    """Тест интеграции с моделью Person."""
    print_section("ТЕСТ 6: Интеграция с моделью Person")
    
    sys.path.insert(0, os.path.join(BASE_DIR, "Дерево"))
    
    try:
        from models import Person
        
        # Создаём персону
        p = Person(name="Тест", surname="Тестов", gender="Мужской")
        
        # Проверяем поле photo_full
        if hasattr(p, 'photo_full'):
            print(f"✓ Поле photo_full существует")
            print(f"  Значение по умолчанию: {p.photo_full}")
        else:
            print(f"✗ Поле photo_full отсутствует!")
            return False
        
        # Устанавливаем фото
        p.photo = "thumbnail_base64_data"
        p.photo_full = "full_base64_data"
        
        if p.photo == "thumbnail_base64_data" and p.photo_full == "full_base64_data":
            print(f"✓ Установка photo_full работает")
        else:
            print(f"✗ Ошибка установки")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Запуск всех тестов."""
    print_section("ТЕСТИРОВАНИЕ СИСТЕМЫ ФОТО")
    print(f"Настройки:")
    print(f"  THUMBNAIL_SIZE = {THUMBNAIL_SIZE}")
    print(f"  PREVIEW_SIZE = {PREVIEW_SIZE}")
    print(f"  MAX_FILE_SIZE_KB = {MAX_FILE_SIZE_KB}")
    
    results = []
    
    results.append(("Сжатие", test_compress_image()))
    results.append(("Миниатюра", test_thumbnail()))
    results.append(("Base64", test_base64()))
    results.append(("Данные фото", test_get_photo_data()))
    results.append(("Синхронизация", test_save_photo_for_sync()))
    results.append(("Модель Person", test_model_integration()))
    
    # Итоги
    print_section("ИТОГИ")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Пройдено: {passed}/{total}")
    
    if passed == total:
        print("\n  🎉 Все тесты пройдены!")
        return 0
    else:
        print("\n  ⚠ Некоторые тесты не пройдены")
        return 1


if __name__ == "__main__":
    sys.exit(main())
