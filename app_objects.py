"""
Веб-приложение для учёта объектов + Сметы
"""

from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Импортируем модуль смет
from estimate_module import bp as estimate_bp, init_db as init_estimate_db
app.register_blueprint(estimate_bp)

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "objects.db")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ============================
# БАЗА ДАННЫХ
# ============================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS objects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_start TEXT,
        date_end TEXT,
        name TEXT NOT NULL,
        client TEXT,
        sum_work REAL DEFAULT 0,
        expenses REAL DEFAULT 0,
        status TEXT DEFAULT 'Запланирован',
        advance REAL DEFAULT 0,
        salary REAL DEFAULT 0,
        notes TEXT,
        created_at TEXT,
        updated_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT
    )''')
    
    # Добавляем клиентов если пусто
    c.execute("SELECT COUNT(*) FROM clients")
    if c.fetchone()[0] == 0:
        clients = [
            ("Иванов Иван Иванович", "+375 (29) 123-45-67", "ivanov@mail.ru", "Колодищи, ул. Центральная, 15"),
            ("ООО БелСтрой", "+375 (17) 234-56-78", "info@belstroy.by", "Минский р-н, д. Щемыслица"),
            ("Петров Пётр Петрович", "+375 (33) 345-67-89", "", "СТ Вишня, участок 42"),
            ("Сидоров А.В.", "+375 (25) 567-89-01", "", "Узляны"),
            ("Козлов Д.Д.", "+375 (44) 678-90-12", "", "Дроздово"),
        ]
        c.executemany("INSERT INTO clients (name, phone, email, address) VALUES (?, ?, ?, ?)", clients)
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================
# СТРАНИЦЫ
# ============================
@app.route('/')
def index():
    return render_template('objects/index.html')

# ============================
# API: ОБЪЕКТЫ
# ============================
@app.route('/api/objects', methods=['GET'])
def get_objects():
    conn = get_db()
    objects = [dict(row) for row in conn.execute(
        "SELECT * FROM objects ORDER BY date_start DESC, id DESC"
    ).fetchall()]
    conn.close()
    
    # Считаем остатки и прибыль
    for obj in objects:
        obj['balance'] = obj['sum_work'] - obj['advance']
        obj['profit'] = obj['sum_work'] - obj['expenses'] - obj['salary']
    
    return jsonify(objects)

@app.route('/api/objects', methods=['POST'])
def add_object():
    data = request.json
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO objects 
           (date_start, date_end, name, client, sum_work, expenses, status, advance, salary, notes, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.get('date_start', datetime.now().strftime('%Y-%m-%d')),
            data.get('date_end', ''),
            data.get('name', ''),
            data.get('client', ''),
            data.get('sum_work', 0),
            data.get('expenses', 0),
            data.get('status', 'Запланирован'),
            data.get('advance', 0),
            data.get('salary', 0),
            data.get('notes', ''),
            now,
            now
        )
    )
    conn.commit()
    
    obj_id = cursor.lastrowid
    obj = dict(conn.execute("SELECT * FROM objects WHERE id=?", (obj_id,)).fetchone())
    obj['balance'] = obj['sum_work'] - obj['advance']
    obj['profit'] = obj['sum_work'] - obj['expenses'] - obj['salary']
    conn.close()
    
    return jsonify(obj), 201

@app.route('/api/objects/<int:obj_id>', methods=['PUT'])
def update_object(obj_id):
    data = request.json
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db()
    conn.execute(
        """UPDATE objects SET
           date_start=?, date_end=?, name=?, client=?, sum_work=?, 
           expenses=?, status=?, advance=?, salary=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            data.get('date_start'),
            data.get('date_end'),
            data.get('name'),
            data.get('client'),
            data.get('sum_work'),
            data.get('expenses'),
            data.get('status'),
            data.get('advance'),
            data.get('salary'),
            data.get('notes'),
            now,
            obj_id
        )
    )
    conn.commit()
    
    obj = dict(conn.execute("SELECT * FROM objects WHERE id=?", (obj_id,)).fetchone())
    obj['balance'] = obj['sum_work'] - obj['advance']
    obj['profit'] = obj['sum_work'] - obj['expenses'] - obj['salary']
    conn.close()
    
    return jsonify(obj)

@app.route('/api/objects/<int:obj_id>', methods=['DELETE'])
def delete_object(obj_id):
    conn = get_db()
    conn.execute("DELETE FROM objects WHERE id=?", (obj_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# ============================
# API: КЛИЕНТЫ
# ============================
@app.route('/api/clients', methods=['GET'])
def get_clients():
    conn = get_db()
    clients = [dict(row) for row in conn.execute("SELECT * FROM clients ORDER BY name").fetchall()]
    conn.close()
    return jsonify(clients)

@app.route('/api/clients', methods=['POST'])
def add_client():
    data = request.json
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO clients (name, phone, email, address) VALUES (?, '', '', '')",
            (data.get('name', ''),)
        )
        conn.commit()
        client = dict(conn.execute("SELECT * FROM clients WHERE id=?", (cursor.lastrowid,)).fetchone())
        conn.close()
        return jsonify(client), 201
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

# ============================
# API: СТАТИСТИКА
# ============================
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    
    total = conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM objects WHERE status='В работе'").fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM objects WHERE status='Завершён'").fetchone()[0]
    planned = conn.execute("SELECT COUNT(*) FROM objects WHERE status='Запланирован'").fetchone()[0]
    
    total_sum = conn.execute("SELECT COALESCE(SUM(sum_work), 0) FROM objects").fetchone()[0]
    total_expenses = conn.execute("SELECT COALESCE(SUM(expenses), 0) FROM objects").fetchone()[0]
    total_salary = conn.execute("SELECT COALESCE(SUM(salary), 0) FROM objects").fetchone()[0]
    total_advance = conn.execute("SELECT COALESCE(SUM(advance), 0) FROM objects").fetchone()[0]
    
    conn.close()
    
    profit = total_sum - total_expenses - total_salary
    balance = total_sum - total_advance
    
    return jsonify({
        "total": total,
        "in_progress": in_progress,
        "completed": completed,
        "planned": planned,
        "total_sum": total_sum,
        "total_expenses": total_expenses,
        "total_salary": total_salary,
        "total_advance": total_advance,
        "profit": profit,
        "balance": balance
    })

# ============================
# ЗАПУСК
# ============================
if __name__ == '__main__':
    init_db()
    init_estimate_db()
    print("[OK] Базы данных созданы")
    print("[OK] Запуск сервера...")
    print("[INFO] Откройте: http://localhost:5000")
    print("[INFO] Сметы: http://localhost:5000/estimate/")
    _debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    app.run(debug=_debug, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
