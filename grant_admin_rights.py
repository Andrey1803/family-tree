# -*- coding: utf-8 -*-
"""
Скрипт для предоставления прав администратора пользователю Андрей Емельянов.
Отправляет запрос на сервер Railway.
"""

import json
import urllib.request
import urllib.error
import sys

# Включаем поддержку UTF-8 для Windows консоли
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

def main():
    print("=" * 60)
    print("  Predostavlenie prav administratora")
    print("=" * 60)
    
    # Shag 1: Vhod pod super-adminom
    print("\n1. Vhod pod super-adminom (admin)...")
    
    admin_login = "admin"
    admin_password = "admin123"
    
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/auth/login",
            data=json.dumps({"login": admin_login, "password": admin_password}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            token = data.get('token')
            
            if not token:
                print(f"   [ERROR] {data.get('error', 'Unknown error')}")
                return
            
            print(f"   [OK] Token poluchen")
            
    except urllib.error.HTTPError as e:
        print(f"   [ERROR] HTTP {e.code}: Neverny login ili parol")
        return
    except Exception as e:
        print(f"   [ERROR] {e}")
        return
    
    # Shag 2: Poluchenie spiska polzovateley
    print("\n2. Poluchenie spiska polzovateley...")
    
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/users",
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            users = data.get('users', [])
            
            # Ishchem Andreya Emelyanova
            andrey_user = None
            for user in users:
                if user.get('login') == 'Андрей Емельянов':
                    andrey_user = user
                    break
            
            if not andrey_user:
                print(f"   [ERROR] Polzovatel 'Andrey Emelyanov' ne nayden")
                return
            
            user_id = andrey_user.get('id')
            is_admin = andrey_user.get('is_admin', False)
            
            print(f"   [OK] Nayden polzovatel:")
            print(f"      ID: {user_id}")
            print(f"      Login: {andrey_user.get('login')}")
            print(f"      Tekuschie prava: {'ADMIN' if is_admin else 'NET PRAV'}")
            
            if is_admin:
                print(f"\n   [INFO] U polzovatelya UZHE yest prava administratora!")
                print(f"   Perezapustite prilozhenie i vojdite v admin-panel.")
                return
            
    except Exception as e:
        print(f"   [ERROR] {e}")
        return
    
    # Shag 3: Predostavlenie prav administratora
    print("\n3. Predostavlenie prav administratora...")
    
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/user/{user_id}/grant-admin",
            headers={'Authorization': f'Bearer {token}'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"   [OK] {data.get('message', 'Prava predostavleny')}")
            
    except urllib.error.HTTPError as e:
        print(f"   [ERROR] HTTP {e.code}")
        error_data = json.loads(e.read().decode()) if e.read else {}
        print(f"      {error_data.get('error', 'Unknown error')}")
        return
    except Exception as e:
        print(f"   [ERROR] {e}")
        return
    
    # Shag 4: Proverka rezultata
    print("\n4. Proverka rezultata...")
    
    try:
        req = urllib.request.Request(
            f"{SYNC_URL}/api/admin/users",
            headers={'Authorization': f'Bearer {token}'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            users = data.get('users', [])
            
            for user in users:
                if user.get('login') == 'Андрей Емельянов':
                    is_admin = user.get('is_admin', False)
                    status = 'ADMIN' if is_admin else 'NET PRAV (OSHBKA!)'
                    print(f"   [RESULT] Prava administratora: {status}")
                    break
            
    except Exception as e:
        print(f"   [ERROR] {e}")
        return
    
    print("\n" + "=" * 60)
    print("  GOTOVO! Teper mozhno voiti v admin-panel")
    print("=" * 60)
    print("\nPerzapustite prilozhenie i otkroyte:")
    print("  Menyu Fajl -> Admin-panel")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Prervano polzovatelem")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
