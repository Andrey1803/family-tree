# -*- coding: utf-8 -*-
import urllib.request
import json

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"

token_req = urllib.request.Request(
    f"{SYNC_URL}/api/auth/login",
    data=json.dumps({"login": "Наталья Емельянова", "password": "130196"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
token_resp = urllib.request.urlopen(token_req)
token = json.loads(token_resp.read())["token"]

tree_req = urllib.request.Request(
    f"{SYNC_URL}/api/sync/download",
    headers={"Authorization": f"Bearer {token}"}
)
tree_resp = urllib.request.urlopen(tree_req)
tree = json.loads(tree_resp.read())["tree"]

print(f"Дерево Натальи: {len(tree.get('persons', {}))} персон")
for pid, p in tree.get("persons", {}).items():
    print(f"  [{pid}] {p.get('surname')} {p.get('name')}")
