-- ============================================
-- СКРИПТ ДЛЯ ПРОВЕРКИ И ИСПРАВЛЕНИЯ БД
-- ============================================

-- 1. Показать всех пользователей
SELECT id, login, email, is_admin, is_active, created_at 
FROM users 
ORDER BY created_at DESC;

-- 2. Найти дубликаты логинов
SELECT login, COUNT(*) as count, array_agg(id) as user_ids
FROM users 
GROUP BY login 
HAVING COUNT(*) > 1;

-- 3. Показать деревья и их владельцев
SELECT 
    ft.id as tree_id,
    ft.name as tree_name,
    ft.user_id,
    u.login as owner_login,
    COUNT(p.id) as person_count
FROM family_trees ft
LEFT JOIN users u ON ft.user_id = u.id
LEFT JOIN persons p ON p.tree_id = ft.id
GROUP BY ft.id, ft.name, ft.user_id, u.login
ORDER BY ft.id;

-- 4. Найти деревья без владельцев (осиротелые)
SELECT ft.* 
FROM family_trees ft
LEFT JOIN users u ON ft.user_id = u.id
WHERE u.id IS NULL;

-- 5. Удалить дубликаты пользователей (оставить только последнего)
-- ВНИМАНИЕ: Сначала проверьте результаты запроса выше!
-- DELETE FROM users 
-- WHERE id IN (
--     SELECT id FROM (
--         SELECT id, ROW_NUMBER() OVER (PARTITION BY login ORDER BY created_at DESC) as rn
--         FROM users
--     ) t
--     WHERE rn > 1
-- );

-- 6. Удалить осиротелые деревья
-- DELETE FROM family_trees WHERE user_id NOT IN (SELECT id FROM users);
