-- Скрипт для предоставления прав администратора пользователю "Андрей Емельянов"
-- Выполнить на сервере Railway через Railway CLI или панель управления

-- === ШАГ 1: Проверить, существует ли пользователь ===
SELECT id, login, is_admin FROM users WHERE login = 'Андрей Емельянов';

-- === ШАГ 2: Если пользователь существует, обновляем его права ===
UPDATE users SET is_admin = 1 WHERE login = 'Андрей Емельянов';

-- === ШАГ 3: Проверить результат ===
SELECT id, login, is_admin FROM users WHERE login = 'Андрей Емельянов';

-- === ШАГ 4: Показать всех администраторов ===
SELECT id, login, email, is_admin, is_active, created_at FROM users WHERE is_admin = 1;

-- === Альтернативно: предоставить права через Railway CLI ===
-- railway run sqlite3 /data/family_tree.db "UPDATE users SET is_admin = 1 WHERE login = 'Андрей Емельянов';"
