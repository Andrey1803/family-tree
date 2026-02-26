# -*- coding: utf-8 -*-
"""
Сервис резервного копирования.
Расширяет базовый backup.py с улучшенной архитектурой.
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Настройки
AUTO_SAVE_INTERVAL = 300  # 5 минут
MAX_BACKUPS = 10


class BackupService:
    """Сервис для управления резервными копиями."""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Инициализация сервиса.

        Args:
            data_dir: Директория для данных. Если None, используется текущая.
        """
        self.data_dir = Path(data_dir) if data_dir else Path.cwd()
        self.backup_dir = self.data_dir / "backups"
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Создаёт папку для бэкапов, если она не существует."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Папка бэкапов: {self.backup_dir}")
        except Exception as e:
            logger.error(f"Ошибка создания папки бэкапов: {e}")

    def create_backup(self, file_path: str, prefix: str = "backup") -> Optional[str]:
        """
        Создаёт резервную копию файла.

        Args:
            file_path: Путь к файлу для бэкапа.
            prefix: Префикс имени файла бэкапа.

        Returns:
            Путь к созданному бэкапу или None в случае ошибки.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.warning(f"Файл для бэкапа не найден: {file_path}")
            return None

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"{prefix}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_filename

            shutil.copy2(file_path, backup_path)
            logger.info(f"Бэкап создан: {backup_path}")

            # Удаляем старые бэкапы
            self._cleanup_old_backups(prefix)

            return str(backup_path)

        except Exception as e:
            logger.error(f"Ошибка создания бэкапа: {e}")
            return None

    def _cleanup_old_backups(self, prefix: str):
        """
        Удаляет старые бэкапы, оставляя только MAX_BACKUPS последних.

        Args:
            prefix: Префикс для фильтрации бэкапов.
        """
        try:
            pattern = f"{prefix}_*"
            backups = sorted(
                self.backup_dir.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            for old_backup in backups[MAX_BACKUPS:]:
                try:
                    old_backup.unlink()
                    logger.info(f"Удалён старый бэкап: {old_backup}")
                except Exception as e:
                    logger.warning(f"Ошибка удаления бэкапа {old_backup}: {e}")

        except Exception as e:
            logger.error(f"Ошибка очистки старых бэкапов: {e}")

    def list_backups(self, prefix: str = "backup") -> List[Dict[str, Any]]:
        """
        Возвращает список всех бэкапов.

        Args:
            prefix: Префикс для фильтрации.

        Returns:
            Список словарей с информацией о бэкапах.
        """
        backups = []
        try:
            pattern = f"{prefix}_*"
            for backup_path in sorted(self.backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
                stat = backup_path.stat()
                backups.append({
                    "path": str(backup_path),
                    "name": backup_path.name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime),
                    "timestamp": stat.st_mtime,
                })
        except Exception as e:
            logger.error(f"Ошибка списка бэкапов: {e}")

        return backups

    def delete_backup(self, backup_path: str) -> bool:
        """
        Удаляет указанный бэкап.

        Args:
            backup_path: Путь к бэкапу.

        Returns:
            True если успешно.
        """
        try:
            path = Path(backup_path)
            if path.exists():
                path.unlink()
                logger.info(f"Бэкап удалён: {backup_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка удаления бэкапа: {e}")
            return False

    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """
        Восстанавливает файл из бэкапа.

        Args:
            backup_path: Путь к бэкапу.
            target_path: Путь для восстановления.

        Returns:
            True если успешно.
        """
        try:
            src = Path(backup_path)
            dst = Path(target_path)

            if not src.exists():
                logger.error(f"Бэкап не найден: {backup_path}")
                return False

            shutil.copy2(src, dst)
            logger.info(f"Восстановлено из бэкапа: {backup_path} -> {target_path}")
            return True

        except Exception as e:
            logger.error(f"Ошибка восстановления из бэкапа: {e}")
            return False

    def get_backup_info(self) -> Dict[str, Any]:
        """
        Возвращает общую информацию о бэкапах.

        Returns:
            Словарь с информацией: {count, total_size, oldest, newest, interval_minutes}.
        """
        try:
            backups = self.list_backups()
            if not backups:
                return {
                    "count": 0,
                    "total_size": 0,
                    "oldest": None,
                    "newest": None,
                    "interval_minutes": AUTO_SAVE_INTERVAL // 60,
                }

            total_size = sum(b["size"] for b in backups)
            return {
                "count": len(backups),
                "total_size": total_size,
                "oldest": backups[-1]["created"] if backups else None,
                "newest": backups[0]["created"] if backups else None,
                "interval_minutes": AUTO_SAVE_INTERVAL // 60,
            }

        except Exception as e:
            logger.error(f"Ошибка получения информации о бэкапах: {e}")
            return {
                "count": 0,
                "total_size": 0,
                "oldest": None,
                "newest": None,
                "interval_minutes": AUTO_SAVE_INTERVAL // 60,
            }

    def should_auto_save(self, last_save_time: Optional[float]) -> bool:
        """
        Проверяет, пора ли делать автосохранение.

        Args:
            last_save_time: Время последнего сохранения (timestamp).

        Returns:
            True если пора делать автосохранение.
        """
        if last_save_time is None:
            return True

        elapsed = datetime.now().timestamp() - last_save_time
        return elapsed >= AUTO_SAVE_INTERVAL
