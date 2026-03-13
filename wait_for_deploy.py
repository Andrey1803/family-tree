# -*- coding: utf-8 -*-
"""Проверка доступности сервера с ожиданием"""

import time
import urllib.request
import json

BASE_URL = "https://family-tree-production-0e7d.up.railway.app"

print("Ожидание готовности сервера...")
print("-" * 60)

for i in range(10):
    try:
        req = urllib.request.Request(f"{BASE_URL}/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                print(f"\n✅ СЕРВЕР ГОТОВ (попытка {i+1})")
                print(f"   Статус: {resp.status}")
                
                # Проверяем CORS заголовки
                cors_header = resp.getheader('Access-Control-Allow-Origin')
                if cors_header:
                    print(f"   CORS: {cors_header}")
                else:
                    print(f"   CORS: заголовок не найден (может быть на других эндпоинтах)")
                
                break
    except Exception as e:
        print(f"Попытка {i+1}: Сервер ещё не готов... ({e})")
        time.sleep(15)  # Ждём 15 секунд между попытками
else:
    print("\n❌ Сервер не ответил за 2.5 минуты")
    print("   Проверьте Railway Dashboard: https://railway.app/")
