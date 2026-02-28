# -*- coding: utf-8 -*-
"""
Сервер синхронизации для приложения "Семейное древо".
REST API для синхронизации между desktop и web версиями.
"""

import json
import os
import sys
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

from flask import Flask, request, jsonify, session, g
from flask_cors import CORS
import sqlite3

# === КОНФИГУРАЦИЯ ===
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
CORS(app, supports_credentials=True)

# Пути к данным
DATA_DIR = os.environ.get("DATA_DIR") or os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DATA_DIR, "family_tree.db")

# === БАЗА ДАННЫХ ===
def get_db():
    """Получить соединение с БД."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Закрыть соединение с БД."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Инициализировать базу данных."""
    DB_FILE = os.environ.get('DATA_DIR', '.') + '/family_tree.db'
    db = sqlite3.connect(DB_FILE)

    # Таблица пользователей
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    
    # Таблица деревьев
    db.execute('''
        CREATE TABLE IF NOT EXISTS family_trees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Таблица персон
    db.execute('''
        CREATE TABLE IF NOT EXISTS persons (
            id TEXT PRIMARY KEY,
            tree_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            patronymic TEXT,
            birth_date TEXT,
            death_date TEXT,
            is_deceased BOOLEAN DEFAULT 0,
            gender TEXT,
            photo_path TEXT,
            photo BLOB,
            birth_place TEXT,
            biography TEXT,
            burial_place TEXT,
            burial_date TEXT,
            occupation TEXT,
            education TEXT,
            address TEXT,
            notes TEXT,
            phone TEXT,
            email TEXT,
            vk TEXT,
            telegram TEXT,
            whatsapp TEXT,
            blood_type TEXT,
            rh_factor TEXT,
            allergies TEXT,
            chronic_conditions TEXT,
            links TEXT,
            photo_album TEXT,
            parents TEXT,
            children TEXT,
            spouse_ids TEXT,
            collapsed_branches BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tree_id) REFERENCES family_trees (id) ON DELETE CASCADE
        )
    ''')
    
    # Таблица браков
    db.execute('''
        CREATE TABLE IF NOT EXISTS marriages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tree_id INTEGER NOT NULL,
            person1_id TEXT NOT NULL,
            person2_id TEXT NOT NULL,
            marriage_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tree_id) REFERENCES family_trees (id) ON DELETE CASCADE
        )
    ''')
    
    # Таблица сессий для отслеживания активности
    db.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Таблица логов синхронизации
    db.execute('''
        CREATE TABLE IF NOT EXISTS sync_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            entities_count INTEGER,
            sync_duration_ms INTEGER,
            status TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Индексы для ускорения поиска
    db.execute('CREATE INDEX IF NOT EXISTS idx_persons_tree ON persons(tree_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_marriages_tree ON marriages(tree_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_users_login ON users(login)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_sync_logs_user ON sync_logs(user_id)')
    
    # Создадим администратора по умолчанию (логин: admin, пароль: admin123)
    admin_password = _password_hash("admin", "admin123")
    db.execute('''
        INSERT OR IGNORE INTO users (login, password_hash, email, is_admin)
        VALUES (?, ?, ?, ?)
    ''', ("admin", admin_password, "admin@familytree.local", 1))
    
    db.commit()
    db.close()

def _password_hash(login: str, password: str) -> str:
    """Создать хеш пароля."""
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        raw = f"FamilyTreeApp_v1{login}{password}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

def _verify_password(login: str, password: str, stored_hash: str) -> bool:
    """Проверить пароль."""
    if stored_hash.startswith("$2"):
        if BCRYPT_AVAILABLE:
            try:
                return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
            except:
                return False
        return False
    else:
        raw = f"FamilyTreeApp_v1{login}{password}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest() == stored_hash

# === ДЕКОРАТОРЫ ===
def require_auth(f):
    """Требует аутентификацию."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Требуется авторизация'}), 401
        
        token = token[7:]
        db = get_db()
        session = db.execute(
            'SELECT user_id FROM user_sessions WHERE session_token = ? AND last_activity > datetime("now", "-24 hours")',
            (token,)
        ).fetchone()
        
        if not session:
            return jsonify({'error': 'Неверный токен или истёк срок действия'}), 401
        
        g.current_user_id = session['user_id']
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    """Требует права администратора."""
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        db = get_db()
        user = db.execute('SELECT is_admin FROM users WHERE id = ?', (g.current_user_id,)).fetchone()
        
        if not user or not user['is_admin']:
            return jsonify({'error': 'Требуется права администратора'}), 403
        
        return f(*args, **kwargs)
    return decorated

# === API АУТЕНТИФИКАЦИИ ===
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Регистрация нового пользователя."""
    data = request.get_json()
    login = data.get('login', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    
    if not login or len(login) < 3:
        return jsonify({'error': 'Логин должен быть не менее 3 символов'}), 400
    
    if not password or len(password) < 6:
        return jsonify({'error': 'Пароль должен быть не менее 6 символов'}), 400
    
    db = get_db()
    
    # Проверка существования
    existing = db.execute('SELECT id FROM users WHERE login = ?', (login,)).fetchone()
    if existing:
        return jsonify({'error': 'Пользователь с таким логином уже существует'}), 409
    
    # Создание пользователя
    password_hash = _password_hash(login, password)
    db.execute(
        'INSERT INTO users (login, password_hash, email) VALUES (?, ?, ?)',
        (login, password_hash, email)
    )
    db.commit()
    
    return jsonify({'message': 'Пользователь успешно зарегистрирован'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Вход в систему."""
    data = request.get_json()
    login = data.get('login', '').strip()
    password = data.get('password', '')
    
    db = get_db()
    user = db.execute('SELECT id, password_hash FROM users WHERE login = ? AND is_active = 1', (login,)).fetchone()
    
    if not user or not _verify_password(login, password, user['password_hash']):
        return jsonify({'error': 'Неверный логин или пароль'}), 401
    
    # Обновление времени последнего входа
    db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
    
    # Создание сессии
    session_token = secrets.token_urlsafe(32)
    db.execute(
        'INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent) VALUES (?, ?, ?, ?)',
        (user['id'], session_token, request.remote_addr, request.user_agent.string)
    )
    db.commit()
    
    return jsonify({
        'token': session_token,
        'user_id': user['id'],
        'expires_in': 86400  # 24 часа
    })

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Выход из системы."""
    token = request.headers.get('Authorization')[7:]
    db = get_db()
    db.execute('DELETE FROM user_sessions WHERE session_token = ?', (token,))
    db.commit()
    
    return jsonify({'message': 'Выход выполнен успешно'})

# === API СИНХРОНИЗАЦИИ ===
@app.route('/api/sync/upload', methods=['POST'])
@require_auth
def sync_upload():
    """Загрузка данных дерева на сервер."""
    data = request.get_json()
    tree_data = data.get('tree', {})
    tree_name = data.get('tree_name', 'Моё дерево')
    
    db = get_db()
    start_time = datetime.now()
    
    try:
        # Получаем или создаём дерево
        tree = db.execute(
            'SELECT id FROM family_trees WHERE user_id = ?',
            (g.current_user_id,)
        ).fetchone()
        
        if tree:
            tree_id = tree['id']
            db.execute('UPDATE family_trees SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (tree_id,))
        else:
            cursor = db.execute(
                'INSERT INTO family_trees (user_id, name) VALUES (?, ?)',
                (g.current_user_id, tree_name)
            )
            tree_id = cursor.lastrowid
        
        # Очищаем старые данные
        db.execute('DELETE FROM persons WHERE tree_id = ?', (tree_id,))
        db.execute('DELETE FROM marriages WHERE tree_id = ?', (tree_id,))
        
        # Вставляем персоны
        persons = tree_data.get('persons', {})
        for pid, pdata in persons.items():
            links_json = json.dumps(pdata.get('links', []))
            photo_album_json = json.dumps(pdata.get('photo_album', []))
            parents_json = json.dumps(list(pdata.get('parents', [])))
            children_json = json.dumps(list(pdata.get('children', [])))
            spouse_ids_json = json.dumps(list(pdata.get('spouse_ids', [])))
            
            db.execute('''
                INSERT INTO persons (
                    id, tree_id, name, surname, patronymic, birth_date, death_date,
                    is_deceased, gender, photo_path, photo, birth_place, biography,
                    burial_place, burial_date, occupation, education, address, notes,
                    phone, email, vk, telegram, whatsapp, blood_type, rh_factor,
                    allergies, chronic_conditions, links, photo_album, parents,
                    children, spouse_ids, collapsed_branches
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pid, tree_id,
                pdata.get('name', ''),
                pdata.get('surname', ''),
                pdata.get('patronymic', ''),
                pdata.get('birth_date', ''),
                pdata.get('death_date', ''),
                1 if pdata.get('is_deceased') else 0,
                pdata.get('gender', ''),
                pdata.get('photo_path', ''),
                pdata.get('photo'),
                pdata.get('birth_place', ''),
                pdata.get('biography', ''),
                pdata.get('burial_place', ''),
                pdata.get('burial_date', ''),
                pdata.get('occupation', ''),
                pdata.get('education', ''),
                pdata.get('address', ''),
                pdata.get('notes', ''),
                pdata.get('phone', ''),
                pdata.get('email', ''),
                pdata.get('vk', ''),
                pdata.get('telegram', ''),
                pdata.get('whatsapp', ''),
                pdata.get('blood_type', ''),
                pdata.get('rh_factor', ''),
                pdata.get('allergies', ''),
                pdata.get('chronic_conditions', ''),
                links_json,
                photo_album_json,
                parents_json,
                children_json,
                spouse_ids_json,
                1 if pdata.get('collapsed_branches') else 0
            ))
        
        # Вставляем браки
        marriages = tree_data.get('marriages', [])
        if isinstance(marriages, list):
            for marriage in marriages:
                if isinstance(marriage, dict):
                    persons_list = marriage.get('persons', [])
                    if len(persons_list) >= 2:
                        db.execute('''
                            INSERT INTO marriages (tree_id, person1_id, person2_id, marriage_date)
                            VALUES (?, ?, ?, ?)
                        ''', (tree_id, persons_list[0], persons_list[1], marriage.get('date', '')))
                elif isinstance(marriage, (list, tuple)) and len(marriage) >= 2:
                    db.execute('''
                        INSERT INTO marriages (tree_id, person1_id, person2_id)
                        VALUES (?, ?, ?)
                    ''', (tree_id, marriage[0], marriage[1]))
        
        db.commit()
        
        # Лог синхронизации
        duration = int((datetime.now() - start_time).total_seconds() * 1000)
        db.execute('''
            INSERT INTO sync_logs (user_id, action, entities_count, sync_duration_ms, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (g.current_user_id, 'upload', len(persons), duration, 'success'))
        db.commit()
        
        return jsonify({'message': 'Синхронизация успешна', 'persons_count': len(persons)})
    
    except Exception as e:
        db.rollback()
        db.execute('''
            INSERT INTO sync_logs (user_id, action, status, error_message)
            VALUES (?, ?, ?, ?)
        ''', (g.current_user_id, 'upload', 'error', str(e)))
        db.commit()
        
        return jsonify({'error': f'Ошибка синхронизации: {str(e)}'}), 500

@app.route('/api/sync/download', methods=['GET'])
@require_auth
def sync_download():
    """Скачивание данных дерева с сервера."""
    db = get_db()
    
    tree = db.execute(
        'SELECT id, name FROM family_trees WHERE user_id = ?',
        (g.current_user_id,)
    ).fetchone()
    
    if not tree:
        return jsonify({'tree': {'persons': {}, 'marriages': []}})
    
    tree_id = tree['id']
    
    # Получаем персоны
    persons = {}
    for row in db.execute('SELECT * FROM persons WHERE tree_id = ?', (tree_id,)):
        pid = row['id']
        persons[pid] = {
            'name': row['name'],
            'surname': row['surname'],
            'patronymic': row['patronymic'] or '',
            'birth_date': row['birth_date'] or '',
            'death_date': row['death_date'] or '',
            'is_deceased': bool(row['is_deceased']),
            'gender': row['gender'] or '',
            'photo_path': row['photo_path'] or '',
            'photo': row['photo'],
            'birth_place': row['birth_place'] or '',
            'biography': row['biography'] or '',
            'burial_place': row['burial_place'] or '',
            'burial_date': row['burial_date'] or '',
            'occupation': row['occupation'] or '',
            'education': row['education'] or '',
            'address': row['address'] or '',
            'notes': row['notes'] or '',
            'phone': row['phone'] or '',
            'email': row['email'] or '',
            'vk': row['vk'] or '',
            'telegram': row['telegram'] or '',
            'whatsapp': row['whatsapp'] or '',
            'blood_type': row['blood_type'] or '',
            'rh_factor': row['rh_factor'] or '',
            'allergies': row['allergies'] or '',
            'chronic_conditions': row['chronic_conditions'] or '',
            'links': json.loads(row['links'] or '[]'),
            'photo_album': json.loads(row['photo_album'] or '[]'),
            'parents': json.loads(row['parents'] or '[]'),
            'children': json.loads(row['children'] or '[]'),
            'spouse_ids': json.loads(row['spouse_ids'] or '[]'),
            'collapsed_branches': bool(row['collapsed_branches'])
        }
    
    # Получаем браки
    marriages = []
    for row in db.execute('SELECT * FROM marriages WHERE tree_id = ?', (tree_id,)):
        marriages.append({
            'persons': [row['person1_id'], row['person2_id']],
            'date': row['marriage_date'] or ''
        })
    
    return jsonify({
        'tree': {
            'persons': persons,
            'marriages': marriages
        },
        'tree_name': tree['name']
    })

# === АДМИН ПАНЕЛЬ ===
@app.route('/api/admin/stats', methods=['GET'])
@require_admin
def admin_stats():
    """Получение статистики системы."""
    db = get_db()
    
    # Общая статистика
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    active_users = db.execute('SELECT COUNT(*) FROM users WHERE is_active = 1').fetchone()[0]
    total_trees = db.execute('SELECT COUNT(*) FROM family_trees').fetchone()[0]
    total_persons = db.execute('SELECT COUNT(*) FROM persons').fetchone()[0]
    
    # Активные сессии
    active_sessions = db.execute('''
        SELECT COUNT(DISTINCT user_id) FROM user_sessions 
        WHERE last_activity > datetime("now", "-1 hour")
    ''').fetchone()[0]
    
    # Последние регистрации
    recent_users = db.execute('''
        SELECT login, email, created_at FROM users 
        ORDER BY created_at DESC LIMIT 10
    ''').fetchall()
    
    # Логи синхронизации
    recent_syncs = db.execute('''
        SELECT u.login, s.action, s.entities_count, s.status, s.created_at
        FROM sync_logs s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.created_at DESC LIMIT 20
    ''').fetchall()
    
    # Статистика по дням
    daily_stats = db.execute('''
        SELECT 
            date(created_at) as date,
            COUNT(*) as sync_count,
            SUM(entities_count) as total_entities
        FROM sync_logs
        WHERE created_at > datetime("now", "-30 days")
        GROUP BY date(created_at)
        ORDER BY date DESC
    ''').fetchall()
    
    return jsonify({
        'overview': {
            'total_users': total_users,
            'active_users': active_users,
            'total_trees': total_trees,
            'total_persons': total_persons,
            'active_sessions': active_sessions
        },
        'recent_users': [dict(row) for row in recent_users],
        'recent_syncs': [dict(row) for row in recent_syncs],
        'daily_stats': [dict(row) for row in daily_stats]
    })

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def admin_users():
    """Список всех пользователей."""
    db = get_db()
    users = db.execute('''
        SELECT id, login, email, created_at, last_login, is_active, is_admin
        FROM users ORDER BY created_at DESC
    ''').fetchall()
    
    return jsonify({'users': [dict(row) for row in users]})

@app.route('/api/admin/user/<int:user_id>/toggle', methods=['POST'])
@require_admin
def admin_toggle_user(user_id):
    """Активировать/деактивировать пользователя."""
    db = get_db()
    db.execute('UPDATE users SET is_active = NOT is_active WHERE id = ?', (user_id,))
    db.commit()

    return jsonify({'message': 'Статус пользователя изменён'})

@app.route('/api/admin/user/<int:user_id>/trees', methods=['GET'])
@require_admin
def admin_get_user_trees(user_id):
    """Получить деревья пользователя."""
    db = get_db()
    
    # Проверяем существование пользователя
    user = db.execute('SELECT id, login FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Получаем деревья пользователя
    trees = db.execute('''
        SELECT id, name, created_at, updated_at
        FROM family_trees
        WHERE user_id = ?
        ORDER BY updated_at DESC
    ''', (user_id,)).fetchall()
    
    trees_data = []
    for tree in trees:
        # Получаем персон для этого дерева
        persons = db.execute('''
            SELECT id, name, surname, patronymic, gender, birth_date,
                   is_deceased, death_date, parents, children, spouse_ids
            FROM persons
            WHERE tree_id = ?
        ''', (tree['id'],)).fetchall()
        
        # Получаем браки
        marriages = db.execute('''
            SELECT person1_id, person2_id, marriage_date
            FROM marriages
            WHERE tree_id = ?
        ''', (tree['id'],)).fetchall()
        
        tree_data = {
            'id': tree['id'],
            'name': tree['name'],
            'created_at': tree['created_at'],
            'updated_at': tree['updated_at'],
            'persons': {p['id']: {
                'id': p['id'],
                'name': p['name'],
                'surname': p['surname'],
                'patronymic': p['patronymic'],
                'gender': p['gender'],
                'birth_date': p['birth_date'],
                'is_deceased': bool(p['is_deceased']),
                'death_date': p['death_date'],
                'parents': json.loads(p['parents']) if p['parents'] else [],
                'children': json.loads(p['children']) if p['children'] else [],
                'spouse_ids': json.loads(p['spouse_ids']) if p['spouse_ids'] else [],
            } for p in persons},
            'marriages': [{
                'persons': [m['person1_id'], m['person2_id']],
                'date': m['marriage_date']
            } for m in marriages]
        }
        
        trees_data.append(tree_data)
    
    return jsonify({'trees': trees_data})

# === ЗДОРОВЬЕ ПРИЛОЖЕНИЯ ===
@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка здоровья приложения."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if get_db() else 'disconnected'
    })

# === ИНИЦИАЛИЗАЦИЯ ===
def initialize_database():
    """Инициализация БД при старте"""
    import sqlite3
    # Используем DATA_DIR из переменных окружения
    db_dir = os.environ.get('DATA_DIR', '/data')
    DB_FILE = os.path.join(db_dir, 'family_tree.db')
    
    print(f"📦 DB_DIR: {db_dir}")
    print(f"📦 DB_FILE: {DB_FILE}")
    
    # Создаём директорию если нет
    try:
        os.makedirs(db_dir, exist_ok=True)
        print(f"📦 Dir exists: {os.path.exists(db_dir)}")
    except Exception as e:
        print(f"⚠️  Dir create error: {e}")
    
    # Проверяем есть ли таблица users
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("📦 Инициализация базы данных...")
            conn.close()
            init_db()
            print("✅ База данных инициализирована!")
        else:
            # Проверяем количество пользователей
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            print(f"✅ База данных уже инициализирована. Пользователей: {count}")
            # Выводим логинов
            cursor.execute('SELECT login FROM users')
            for row in cursor.fetchall():
                print(f"   - {row[0]}")
        conn.close()
    except Exception as e:
        print(f"❌ DB error: {e}")
        print("📦 Попытка создания БД...")
        try:
            init_db()
            print("✅ База данных создана!")
        except Exception as e2:
            print(f"❌ DB create error: {e2}")

# Авто-инициализация при импорте
initialize_database()

if __name__ == '__main__':
    # Инициализация БД
    initialize_database()
    
    # Запуск сервера
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    print(f"🚀 Запуск сервера на порту {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)
 
