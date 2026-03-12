# -*- coding: utf-8 -*-
"""Сервис работы с фото: сжатие, миниатюры, base64."""

import base64
import io
import os

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# Размеры для миниатюр
THUMBNAIL_SIZE = (200, 200)  # Для карточки персоны
PREVIEW_SIZE = (800, 800)    # Для просмотра в диалоге
MAX_FILE_SIZE_KB = 100       # Максимальный размер миниатюры в KB


def compress_image(image_path, max_size=PREVIEW_SIZE, quality=85):
    """
    Сжимает изображение до указанного размера.
    
    Args:
        image_path: Путь к исходному изображению
        max_size: Максимальный размер (ширина, высота)
        quality: Качество JPEG (1-100)
    
    Returns:
        bytes: Сжатые данные изображения или None при ошибке
    """
    if not PIL_AVAILABLE:
        print("[PHOTO_SERVICE] PIL не доступен, возвращаем исходный файл")
        try:
            with open(image_path, "rb") as f:
                return f.read()
        except Exception:
            return None
    
    try:
        with Image.open(image_path) as img:
            # Конвертируем в RGB (если есть альфа-канал)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Поворачиваем по EXIF (для фото с телефонов)
            img = _exif_transpose(img)
            
            # Уменьшаем размер
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Сохраняем в буфер
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
            
            result = buffer.getvalue()
            print(f"[PHOTO_SERVICE] Сжато {image_path}: {len(result) // 1024} KB")
            return result
            
    except Exception as e:
        print(f"[PHOTO_SERVICE] Ошибка сжатия {image_path}: {e}")
        return None


def create_thumbnail(image_path, size=THUMBNAIL_SIZE, quality=75):
    """
    Создаёт миниатюру изображения для синхронизации.
    
    Args:
        image_path: Путь к исходному изображению
        size: Размер миниатюры
        quality: Качество JPEG
    
    Returns:
        bytes: Данные миниатюры или None при ошибке
    """
    if not os.path.exists(image_path):
        print(f"[PHOTO_SERVICE] Файл не найден: {image_path}")
        return None
    
    return compress_image(image_path, max_size=size, quality=quality)


def image_to_base64(image_data):
    """
    Конвертирует байты изображения в base64 строку.
    
    Args:
        image_data: Байты изображения
    
    Returns:
        str: Base64 строка или None при ошибке
    """
    if not image_data:
        return None
    
    try:
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"[PHOTO_SERVICE] Ошибка base64 кодирования: {e}")
        return None


def base64_to_image(base64_string):
    """
    Конвертирует base64 строку в байты изображения.
    
    Args:
        base64_string: Base64 строка
    
    Returns:
        bytes: Байты изображения или None при ошибке
    """
    if not base64_string:
        return None
    
    try:
        return base64.b64decode(base64_string)
    except Exception as e:
        print(f"[PHOTO_SERVICE] Ошибка base64 декодирования: {e}")
        return None


def save_photo_for_sync(image_path):
    """
    Подготавливает фото для синхронизации: создаёт миниатюру и конвертирует в base64.
    
    Args:
        image_path: Путь к исходному изображению
    
    Returns:
        str: Base64 миниатюра или None при ошибке
    """
    thumbnail_data = create_thumbnail(image_path)
    if not thumbnail_data:
        return None
    
    # Проверяем размер
    if len(thumbnail_data) > MAX_FILE_SIZE_KB * 1024:
        print(f"[PHOTO_SERVICE] Миниатюра слишком большая: {len(thumbnail_data) // 1024} KB")
        # Пробуем с меньшим качеством
        thumbnail_data = create_thumbnail(image_path, quality=60)
    
    return image_to_base64(thumbnail_data)


def _exif_transpose(img):
    """
    Поворачивает изображение по EXIF данным.
    """
    try:
        exif_data = img._getexif()
        if exif_data:
            for orientation in [274]:  # EXIF Orientation tag
                if orientation in exif_data:
                    orientation_value = exif_data[orientation]
                    if orientation_value == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation_value == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation_value == 8:
                        img = img.rotate(90, expand=True)
    except Exception:
        pass
    return img


def get_photo_data(image_path, include_full=False):
    """
    Возвращает данные фото для синхронизации.
    
    Args:
        image_path: Путь к изображению
        include_full: Включать ли полное фото (для локального использования)
    
    Returns:
        dict: {'thumbnail': base64, 'full': base64 (опционально)}
    """
    result = {}
    
    # Миниатюра для сервера
    thumbnail_base64 = save_photo_for_sync(image_path)
    if thumbnail_base64:
        result['thumbnail'] = thumbnail_base64
    
    # Полное фото (сжатое) для локального использования
    if include_full and PIL_AVAILABLE:
        full_data = compress_image(image_path, max_size=PREVIEW_SIZE, quality=85)
        if full_data:
            result['full'] = image_to_base64(full_data)
    elif include_full:
        # Если PIL недоступен, читаем исходный файл
        try:
            with open(image_path, "rb") as f:
                result['full'] = image_to_base64(f.read())
        except Exception:
            pass
    
    return result
