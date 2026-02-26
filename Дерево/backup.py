# -*- coding: utf-8 -*-
"""
Модуль резервного копирования и автосохранения данных.

Автосохранение:
- Сохраняет данные каждые N минут
- Сохраняет при закрытии приложения

Резервные копии:
- Создаёт копию перед каждым сохранением
- Хранит до K последних копий
- Папка: backups/ в директории данных
"""

import os
import shutil
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Настройки
AUTO_SAVE_INTERVAL = 300  # Интервал автосохранения в секундах (5 минут)
MAX_BACKUPS = 10  # Максимальное количество хранимых резервных копий
BACKUP_DIR_NAME = "backups"  # Имя папки для бэкапов


class BackupManager:
    """Управляет резервными копиями и автосохранением."""

    def __init__(self, data_dir=None):
        """
        Инициализация менеджера резервных копий.

        Args:
            data_dir: Директория для хранения данных и бэкапов.
                      Если None, используется текущая рабочая директория.
        """
        self.data_dir = Path(data_dir) if data_dir else Path.cwd()
        self.backup_dir = self.data_dir / BACKUP_DIR_NAME
        self.last_auto_save = None
        self.auto_save_enabled = True
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Создаёт папку для бэкапов, если она не существует."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Папка бэкапов: {self.backup_dir}")
        except Exception as e:
            logger.error(f"Ошибка создания папки бэкапов: {e}")

    def create_backup(self, file_path, backup_name_prefix="backup"):
        """
        Создаёт резервную копию файла.

        Args:
            file_path: Путь к файлу для бэкапа.
            backup_name_prefix: Префикс имени файла бэкапа.

        Returns:
            Путь к созданному бэкапу или None в случае ошибки.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.warning(f"Файл для бэкапа не найден: {file_path}")
            return None

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"{backup_name_prefix}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_filename

            shutil.copy2(file_path, backup_path)
            logger.info(f"Бэкап создан: {backup_path}")

            # Удаляем старые бэкапы
            self._cleanup_old_backups(backup_name_prefix)

            return backup_path
        except Exception as e:
            logger.error(f"Ошибка создания бэкапа: {e}")
            return None

    def _cleanup_old_backups(self, backup_name_prefix):
        """
        Удаляет старые бэкапы, оставляя только MAX_BACKUPS последних.

        Args:
            backup_name_prefix: Префикс для фильтрации бэкапов.
        """
        try:
            pattern = f"{backup_name_prefix}_*"
            backups = sorted(
                self.backup_dir.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Удаляем всё, что выходит за лимит
            for old_backup in backups[MAX_BACKUPS:]:
                old_backup.unlink()
                logger.debug(f"Удалён старый бэкап: {old_backup}")
        except Exception as e:
            logger.error(f"Ошибка очистки старых бэкапов: {e}")

    def restore_from_backup(self, target_file, backup_file=None):
        """
        Восстанавливает файл из резервной копии.

        Args:
            target_file: Путь к файлу для восстановления.
            backup_file: Путь к бэкапу. Если None, используется последний.

        Returns:
            True если успешно, иначе False.
        """
        target_file = Path(target_file)

        if backup_file is None:
            # Ищем последний бэкап
            backups = sorted(
                self.backup_dir.glob("backup_*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if not backups:
                logger.error("Бэкапы не найдены")
                return False
            backup_file = backups[0]
        else:
            backup_file = Path(backup_file)

        if not backup_file.exists():
            logger.error(f"Бэкап не найден: {backup_file}")
            return False

        try:
            shutil.copy2(backup_file, target_file)
            logger.info(f"Восстановлено из бэкапа: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Ошибка восстановления: {e}")
            return False

    def list_backups(self, backup_name_prefix="backup"):
        """
        Возвращает список доступных бэкапов.

        Args:
            backup_name_prefix: Префикс для фильтрации бэкапов.

        Returns:
            Список кортежей (путь, дата_создания).
        """
        pattern = f"{backup_name_prefix}_*"
        backups = []
        for backup_path in self.backup_dir.glob(pattern):
            mtime = datetime.fromtimestamp(backup_path.stat().st_mtime)
            backups.append((backup_path, mtime))
        return sorted(backups, key=lambda x: x[1], reverse=True)

    def should_auto_save(self):
        """
        Проверяет, пора ли делать автосохранение.

        Returns:
            True если прошло больше AUTO_SAVE_INTERVAL секунд.
        """
        if not self.auto_save_enabled:
            return False

        if self.last_auto_save is None:
            return True

        elapsed = (datetime.now() - self.last_auto_save).total_seconds()
        return elapsed >= AUTO_SAVE_INTERVAL

    def mark_auto_save_done(self):
        """Отмечает, что автосохранение выполнено."""
        self.last_auto_save = datetime.now()

    def get_backup_info(self):
        """
        Возвращает информацию о бэкапах для отображения в UI.

        Returns:
            Dict с информацией о бэкапах.
        """
        backups = self.list_backups()
        return {
            "count": len(backups),
            "latest": backups[0][1].strftime("%Y-%m-%d %H:%M") if backups else None,
            "max_allowed": MAX_BACKUPS,
            "interval_minutes": AUTO_SAVE_INTERVAL // 60
        }


class AutoSaveManager:
    """
    Управляет периодическим автосохранением.

    Используется с tkinter.after() для планирования.
    """

    def __init__(self, backup_manager, model, save_callback=None):
        """
        Инициализация менеджера автосохранения.

        Args:
            backup_manager: Экземпляр BackupManager.
            model: Модель данных (FamilyTreeModel).
            save_callback: Функция для вызова при автосохранении.
        """
        self.backup_manager = backup_manager
        self.model = model
        self.save_callback = save_callback
        self.scheduled_job_id = None
        self.root = None  # Будет установлен tkinter root

    def start(self, root):
        """
        Запускает цикл автосохранения.

        Args:
            root: tkinter.Tk экземпляр приложения.
        """
        self.root = root
        self._schedule_auto_save()

    def stop(self):
        """Останавливает цикл автосохранения."""
        if self.scheduled_job_id and self.root:
            self.root.after_cancel(self.scheduled_job_id)
            self.scheduled_job_id = None

    def _schedule_auto_save(self):
        """Планирует следующую проверку автосохранения."""
        if self.root is None:
            return

        if self.backup_manager.should_auto_save():
            self._do_auto_save()

        # Проверяем каждые 60 секунд
        self.scheduled_job_id = self.root.after(60000, self._schedule_auto_save)

    def _do_auto_save(self):
        """Выполняет автосохранение."""
        if not self.model or not self.model.modified:
            self.backup_manager.mark_auto_save_done()
            return

        try:
            # Создаём бэкап перед сохранением
            if self.model.data_file:
                self.backup_manager.create_backup(
                    self.model.data_file,
                    backup_name_prefix="autosave"
                )

            # Сохраняем
            if self.save_callback:
                self.save_callback()

            self.backup_manager.mark_auto_save_done()
            logger.info("Автосохранение выполнено")
        except Exception as e:
            logger.error(f"Ошибка автосохранения: {e}")


def init_backup_system(model, root=None, status_callback=None):
    """
    Инициализирует систему бэкапов и автосохранения.

    Args:
        model: Модель FamilyTreeModel.
        root: tkinter.Tk экземпляр (опционально).
        status_callback: Функция для обновления статуса (опционально).

    Returns:
        Кортеж (BackupManager, AutoSaveManager).
    """
    # Определяем директорию данных
    data_dir = Path(model.data_file).parent if model.data_file else Path.cwd()

    backup_manager = BackupManager(data_dir)
    auto_save_manager = AutoSaveManager(backup_manager, model, model.save_to_file)

    if root:
        auto_save_manager.start(root)

    return backup_manager, auto_save_manager
