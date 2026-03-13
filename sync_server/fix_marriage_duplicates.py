# -*- coding: utf-8 -*-
"""
Очистка дубликатов браков в базе данных.
Запустить в консоли Railway: railway run python fix_marriage_duplicates.py
"""
import sqlite3
import os

DB_FILE = os.environ.get('DATA_DIR', '/data') + '/family_tree.db'

print(f"Connecting to {DB_FILE}...")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Проверяем количество браков
cursor.execute("SELECT COUNT(*) FROM marriages")
total = cursor.fetchone()[0]
print(f"Total marriages: {total}")

# Находим дубликаты
cursor.execute("""
    SELECT tree_id, person1_id, person2_id, COUNT(*) as cnt
    FROM marriages
    GROUP BY tree_id, person1_id, person2_id
    HAVING cnt > 1
""")
duplicates = cursor.fetchall()

if duplicates:
    print(f"\nFound {len(duplicates)} duplicate marriage groups:")
    for dup in duplicates:
        print(f"  tree={dup[0]}, p1={dup[1]}, p2={dup[2]}, count={dup[3]}")
    
    # Удаляем дубликаты (оставляем по 1 записи)
    print("\nRemoving duplicates...")
    for dup in duplicates:
        tree_id, p1, p2 = dup[0], dup[1], dup[2]
        # Оставляем 1 запись, удаляем остальные
        cursor.execute("""
            DELETE FROM marriages
            WHERE tree_id = ? AND person1_id = ? AND person2_id = ?
            AND rowid NOT IN (
                SELECT MIN(rowid)
                FROM marriages
                WHERE tree_id = ? AND person1_id = ? AND person2_id = ?
            )
        """, (tree_id, p1, p2, tree_id, p1, p2))
        deleted = cursor.rowcount
        print(f"  Deleted {deleted} duplicates for tree={tree_id}, p1={p1}, p2={p2}")
    
    conn.commit()
    
    # Проверяем результат
    cursor.execute("SELECT COUNT(*) FROM marriages")
    new_total = cursor.fetchone()[0]
    print(f"\nNew total marriages: {new_total}")
    print(f"Removed {total - new_total} duplicate marriages")
else:
    print("No duplicates found!")

conn.close()
print("\nDone!")
