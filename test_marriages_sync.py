# -*- coding: utf-8 -*-
import urllib.request
import json
import traceback

try:
    # Вход
    req = urllib.request.Request('https://ravishing-caring-production-3656.up.railway.app/api/auth/login',
        data=json.dumps({'login':'Андрей Емельянов','password':'18031981asdF'}).encode(),
        headers={'Content-Type':'application/json'}, method='POST')
    resp = urllib.request.urlopen(req)
    token = json.loads(resp.read())['token']
    print(f'Token получен: {token[:20]}...')

    # Загрузка данных НА сервер
    with open('data/family_tree_Андрей Емельянов.json', 'r', encoding='utf-8') as f:
        local_data = json.load(f)

    print(f'Локально: {len(local_data.get("persons", {}))} персон, {len(local_data.get("marriages", []))} браков')
    print(f'Браки (первые 3): {local_data.get("marriages", [])[:3]}')

    req2 = urllib.request.Request('https://ravishing-caring-production-3656.up.railway.app/api/sync/upload',
        data=json.dumps({'tree': local_data, 'tree_name': 'Дерево Андрей Емельянов'}).encode(),
        headers={'Authorization':f'Bearer {token}', 'Content-Type':'application/json'}, method='POST')
    resp2 = urllib.request.urlopen(req2)
    result = json.loads(resp2.read())
    print(f'Загрузка на сервер: {result}')

    # Скачивание данных С сервера
    req3 = urllib.request.Request('https://ravishing-caring-production-3656.up.railway.app/api/sync/download',
        headers={'Authorization':f'Bearer {token}'})
    resp3 = urllib.request.urlopen(req3)
    data = json.loads(resp3.read())
    tree = data.get('tree', {})
    print(f'Сервер вернул: {len(tree.get("persons", {}))} персон, {len(tree.get("marriages", []))} браков')
    print(f'Браки с сервера: {tree.get("marriages", [])}')
    
except Exception as e:
    print(f'Ошибка: {e}')
    traceback.print_exc()
