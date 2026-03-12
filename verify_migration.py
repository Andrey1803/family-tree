# -*- coding: utf-8 -*-
import sqlite3

DB_FILE = 'sync_server/family_tree.db'
OUTPUT_FILE = 'migration_result.txt'

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(persons)')
    columns = [row[1] for row in cursor.fetchall()]
    
    result = "Columns: " + str(columns) + "\nphoto_full exists: " + str('photo_full' in columns) + "\n"
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print("SUCCESS: " + result)
    conn.close()
except Exception as e:
    error_msg = "ERROR: " + str(e)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(error_msg)
    print(error_msg)
