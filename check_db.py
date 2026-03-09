# -*- coding: utf-8 -*-
"""
Проверка БД на сервере Railway.
"""
import os
import sys

try:
    import psycopg2
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL") or input("Введите DATABASE_URL из Railway: ").strip()

def connect_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Connected to database")
        return conn
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def check_users_and_trees(conn):
    cur = conn.cursor()
    
    print("\n=== USERS AND TREES ===")
    cur.execute("SELECT id, login, email, is_admin, is_active, created_at FROM users ORDER BY id")
    users = cur.fetchall()
    
    for user in users:
        user_id, login, email, is_admin, is_active, created_at = user
        print(f"\nID={user_id}, Login='{login}', Email='{email}', Admin={is_admin}, Active={is_active}")
        
        cur.execute("SELECT id, name, created_at, updated_at FROM family_trees WHERE user_id = %s", (user_id,))
        trees = cur.fetchall()
        
        if trees:
            for tree in trees:
                tree_id, name, created_at, updated_at = tree
                cur.execute("SELECT COUNT(*) FROM persons WHERE tree_id = %s", (tree_id,))
                person_count = cur.fetchone()[0]
                print(f"  Tree ID={tree_id}: '{name}', Persons={person_count}")
        else:
            print(f"  No trees")
    
    cur.close()

def find_duplicates(conn, login_pattern):
    cur = conn.cursor()
    print(f"\n=== SEARCHING FOR: {login_pattern} ===")
    
    cur.execute("SELECT id, login, email, is_active, created_at FROM users WHERE login ILIKE %s ORDER BY created_at DESC", (f"%{login_pattern}%",))
    duplicates = cur.fetchall()
    
    if len(duplicates) > 1:
        print(f"Found {len(duplicates)} duplicates:")
        for user in duplicates:
            print(f"  ID={user[0]}, Login='{user[1]}', Active={user[3]}, Created={user[4]}")
    else:
        print("No duplicates found")
    
    cur.close()

if __name__ == "__main__":
    print("=== DATABASE CHECK ===")
    conn = connect_db()
    if not conn:
        sys.exit(1)
    
    try:
        check_users_and_trees(conn)
        
        login_search = input("\nEnter login to search for duplicates: ").strip()
        if login_search:
            find_duplicates(conn, login_search)
        
        print("\n=== DONE ===")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
