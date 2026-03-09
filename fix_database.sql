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

-- ============================================
-- ИСПРАВЛЕНИЕ: У всех новых пользователей
-- открывается дерево Андрея (проблема с user_id=1)
-- ============================================

-- 7. ПРОВЕРКА: Показать всех пользователей и их деревья
SELECT 
    u.id as user_id,
    u.login,
    ft.id as tree_id,
    ft.name as tree_name,
    COUNT(p.id) as person_count
FROM users u
LEFT JOIN family_trees ft ON u.id = ft.user_id
LEFT JOIN persons p ON p.tree_id = ft.id
GROUP BY u.id, u.login, ft.id, ft.name
ORDER BY u.id;

-- 8. ПРОВЕРКА: Найти пользователей БЕЗ дерева (проблема!)
SELECT u.id, u.login 
FROM users u
LEFT JOIN family_trees ft ON u.id = ft.user_id
WHERE ft.id IS NULL;

-- 9. ИСПРАВЛЕНИЕ: Создать пустые деревья для всех пользователей без дерева
INSERT INTO family_trees (user_id, name)
SELECT u.id, 'Дерево ' || u.login
FROM users u
LEFT JOIN family_trees ft ON u.id = ft.user_id
WHERE ft.id IS NULL;

-- 10. ПРОВЕРКА: Убедиться, что у всех есть деревья
SELECT 
    u.id as user_id,
    u.login,
    ft.id as tree_id,
    ft.name as tree_name
FROM users u
INNER JOIN family_trees ft ON u.id = ft.user_id
ORDER BY u.id;
