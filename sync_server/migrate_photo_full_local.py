#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для выполнения миграции в консоли Railway.
Запустить: railway run python migrate_photo_full_local.py
Или скопировать код в консоль Railway.
"""
import sqlite3
import os

DB_FILE = os.environ.get('DATA_DIR', '/data') + '/family_tree.db'

print(f"Connecting to {DB_FILE}...")

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Проверяем таблицу persons
    cursor.execute("PRAGMA table_info(persons)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"Found {len(columns)} columns in persons table")
    
    migrations_needed = []
    
    if 'photo_full' not in columns:
        migrations_needed.append('photo_full')
    
    if 'created_at' not in columns:
        migrations_needed.append('created_at')
    
    if 'updated_at' not in columns:
        migrations_needed.append('updated_at')
    
    if not migrations_needed:
        print("✅ All migrations already applied!")
    else:
        print(f"Need to add: {', '.join(migrations_needed)}")
        
        for col in migrations_needed:
            print(f"Adding {col}...")
            if col == 'photo_full':
                cursor.execute("ALTER TABLE persons ADD COLUMN photo_full BLOB")
            elif col == 'created_at':
                cursor.execute("ALTER TABLE persons ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            elif col == 'updated_at':
                cursor.execute("ALTER TABLE persons ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print(f"✅ Added {col}")
        
        conn.commit()
        print("✅ Migrations complete!")
    
    # Проверяем результат
    cursor.execute("PRAGMA table_info(persons)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"\nFinal columns: {len(columns)}")
    print("Columns:", columns)
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
