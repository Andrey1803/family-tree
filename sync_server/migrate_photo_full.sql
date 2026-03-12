-- Миграция: добавление колонки photo_full
-- Выполнить в консоли Railway: sqlite3 /data/family_tree.db < migrate_photo_full.sql

-- Проверяем существует ли колонка
SELECT name FROM sqlite_master WHERE type='table' AND name='persons';

-- Добавляем колонку photo_full если не существует
ALTER TABLE persons ADD COLUMN photo_full BLOB;

-- Проверяем результат
PRAGMA table_info(persons);
