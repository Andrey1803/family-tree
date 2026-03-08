# -*- coding: utf-8 -*-
import json
import urllib.request

print('='*60)
print('ТЕСТ 1: Проверка браков на сервере')
print('='*60)
try:
    req = urllib.request.Request('https://ravishing-caring-production-3656.up.railway.app/api/auth/login',
        data=json.dumps({'login':'Андрей Емельянов','password':'18031981asdF'}).encode(),
        headers={'Content-Type':'application/json'}, method='POST')
    resp = urllib.request.urlopen(req)
    token = json.loads(resp.read())['token']
    print(f'[OK] Token получен')
    
    req2 = urllib.request.Request('https://ravishing-caring-production-3656.up.railway.app/api/sync/download',
        headers={'Authorization':f'Bearer {token}'})
    resp2 = urllib.request.urlopen(req2)
    data = json.loads(resp2.read())
    tree = data.get('tree', {})
    print(f'[OK] Персон на сервере: {len(tree.get("persons", {}))}')
    print(f'[OK] Браков на сервере: {len(tree.get("marriages", []))}')
    if tree.get("marriages"):
        print(f'[OK] Первые 3 брака: {tree.get("marriages", [])[:3]}')
except Exception as e:
    print(f'[ERROR] {e}')

print()
print('='*60)
print('ТЕСТ 2: Проверка кода app.py')
print('='*60)
with open('Дерево/app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
if 'Отец... (синий)' in content:
    print('[OK] Цвета для мужчин найдены')
else:
    print('[ERROR] Цвета для мужчин НЕ найдены')
    
if 'Мать... (красный)' in content:
    print('[OK] Цвета для женщин найдены')
else:
    print('[ERROR] Цвета для женщин НЕ найдены')

if 'button_frame.pack(fill=tk.X, side=tk.BOTTOM)' in content:
    print('[OK] Кнопки закреплены внизу')
else:
    print('[ERROR] Кнопки НЕ закреплены')

print()
print('='*60)
print('ТЕСТ 3: Проверка веб-версии (tree.js)')
print('='*60)
with open('web/static/js/tree.js', 'r', encoding='utf-8') as f:
    web_content = f.read()
    
if 'color: "#1e40af"' in web_content:
    print('[OK] Синий цвет найден')
else:
    print('[ERROR] Синий цвет НЕ найден')
    
if 'color: "#dc2626"' in web_content:
    print('[OK] Красный цвет найден')
else:
    print('[ERROR] Красный цвет НЕ найден')
    
if 'Отец' in web_content:
    print('[OK] Текст меню найден')
else:
    print('[ERROR] Текст НЕ найден')

print()
print('='*60)
print('ТЕСТЫ ЗАВЕРШЕНЫ')
print('='*60)
