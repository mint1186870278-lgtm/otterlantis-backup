import sqlite3
import json
import os
import random
import string
from pathlib import Path

DB_PATH = Path(__file__).parent / 'otter.db'
conn = None


def init_db():
    global conn
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            event TEXT NOT NULL,
            user_id INTEGER,
            otter_id TEXT,
            role TEXT,
            payload TEXT,
            ts INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS retention_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            wechat TEXT,
            lang TEXT NOT NULL,
            source TEXT NOT NULL,
            ts INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            otter_id TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL CHECK (role IN ('child', 'guardian')),
            display_name TEXT NOT NULL,
            lang TEXT DEFAULT 'zh',
            email TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TEXT,
            status TEXT DEFAULT 'active'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guardian_child_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guardian_user_id INTEGER NOT NULL,
            child_user_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(guardian_user_id, child_user_id),
            FOREIGN KEY(guardian_user_id) REFERENCES users(id),
            FOREIGN KEY(child_user_id) REFERENCES users(id)
        )
    ''')

    ensure_tracking_user_columns(cursor)

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_session ON tracking_events(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_event ON tracking_events(event)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_otter_id ON tracking_events(otter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_user_id ON tracking_events(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_retention_lang ON retention_submissions(lang)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')

    conn.commit()
    print('Database initialized')


def ensure_tracking_user_columns(cursor):
    cursor.execute('PRAGMA table_info(tracking_events)')
    columns = {row[1] for row in cursor.fetchall()}
    for name, column_type in (
        ('user_id', 'INTEGER'),
        ('otter_id', 'TEXT'),
        ('role', 'TEXT'),
    ):
        if name not in columns:
            cursor.execute(f'ALTER TABLE tracking_events ADD COLUMN {name} {column_type}')


def normalize_otter_id(value):
    if not value:
        return None
    normalized = ''.join(ch for ch in str(value).upper().strip() if ch.isalnum() or ch == '-')
    return normalized or None


def generate_otter_id():
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(20):
        suffix = ''.join(random.choice(alphabet) for _ in range(5))
        otter_id = f'OT-{suffix}'
        if not get_user_by_otter_id(otter_id):
            return otter_id
    raise RuntimeError('Failed to generate unique otter id')


def row_to_user(row):
    if not row:
        return None
    return {
        'id': row[0],
        'otterId': row[1],
        'role': row[2],
        'displayName': row[3],
        'lang': row[4],
        'email': row[5],
        'createdAt': row[6],
        'lastSeenAt': row[7],
        'status': row[8],
    }


def get_user_by_otter_id(otter_id):
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT id, otter_id, role, display_name, lang, email, created_at, last_seen_at, status
        FROM users
        WHERE otter_id = ?
        ''',
        (normalize_otter_id(otter_id),)
    )
    return row_to_user(cursor.fetchone())


def get_user_by_email(email):
    if not email:
        return None
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT id, otter_id, role, display_name, lang, email, created_at, last_seen_at, status
        FROM users
        WHERE lower(email) = lower(?)
        ''',
        (email.strip(),)
    )
    return row_to_user(cursor.fetchone())


def create_user(data):
    role = data['role']
    display_name = data['displayName'].strip()
    lang = data.get('lang') or 'zh'
    email = data.get('email')
    email = email.strip().lower() if email else None
    otter_id = normalize_otter_id(data.get('otterId')) or generate_otter_id()

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO users (otter_id, role, display_name, lang, email)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (otter_id, role, display_name, lang, email)
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError('User already exists') from exc

    return get_user_by_otter_id(otter_id)


def touch_user_seen(user_id):
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET last_seen_at = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
    conn.commit()


def insert_tracking_event(session_id, event, payload, ts):
    cursor = conn.cursor()
    otter_id = normalize_otter_id(payload.get('otterId') or payload.get('otter_id'))
    user = get_user_by_otter_id(otter_id) if otter_id else None
    user_id = user['id'] if user else None
    role = user['role'] if user else payload.get('userRole') or payload.get('role')

    cursor.execute(
        '''
        INSERT INTO tracking_events (session_id, event, user_id, otter_id, role, payload, ts)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (session_id, event, user_id, otter_id, role, json.dumps(payload), ts)
    )
    conn.commit()
    if user_id:
        touch_user_seen(user_id)


def insert_retention_submission(data):
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO retention_submissions (email, wechat, lang, source, ts) VALUES (?, ?, ?, ?, ?)',
        (data.get('email'), data.get('wechat'), data['lang'], data['source'], data['ts'])
    )
    conn.commit()


def get_tracking_stats():
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM tracking_events')
    total = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT session_id) FROM tracking_events')
    sessions = cursor.fetchone()[0]

    cursor.execute('SELECT event, COUNT(*) FROM tracking_events GROUP BY event')
    by_event = [{'event': row[0], 'count': row[1]} for row in cursor.fetchall()]

    return {'total': total, 'sessions': sessions, 'byEvent': by_event}


def list_tracking_events(page=1, page_size=20, session_id=None, event=None):
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if session_id:
        where_clauses.append('session_id = ?')
        params.append(session_id)

    if event:
        where_clauses.append('event = ?')
        params.append(event)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''

    cursor.execute(f'SELECT COUNT(*) FROM tracking_events {where_sql}', params)
    total = cursor.fetchone()[0]

    offset = (page - 1) * page_size
    cursor.execute(
        f'''
        SELECT id, session_id, event, user_id, otter_id, role, payload, ts, created_at
        FROM tracking_events
        {where_sql}
        ORDER BY ts DESC, id DESC
        LIMIT ? OFFSET ?
        ''',
        params + [page_size, offset]
    )

    items = []
    for row in cursor.fetchall():
        payload = {}
        if row[3]:
            try:
                payload = json.loads(row[3])
            except json.JSONDecodeError:
                payload = {'raw': row[3]}

        items.append({
            'id': row[0],
            'sessionId': row[1],
            'event': row[2],
            'userId': row[3],
            'otterId': row[4],
            'role': row[5],
            'payload': payload,
            'ts': row[7],
            'createdAt': row[8],
        })

    return {
        'page': page,
        'pageSize': page_size,
        'total': total,
        'items': items,
    }


def get_user_stats():
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'child'")
    children = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'guardian'")
    guardians = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT child_user_id) FROM guardian_child_links')
    linked_children = cursor.fetchone()[0]

    cursor.execute(
        '''
        SELECT COUNT(*)
        FROM tracking_events
        WHERE event = 'game_start' AND user_id IS NOT NULL
        '''
    )
    total_play_count = cursor.fetchone()[0]
    avg_play_count = round(total_play_count / total, 2) if total else 0

    cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
    by_role = [{'role': row[0], 'count': row[1]} for row in cursor.fetchall()]

    cursor.execute("SELECT lang, COUNT(*) FROM users GROUP BY lang")
    by_lang = [{'lang': row[0], 'count': row[1]} for row in cursor.fetchall()]

    return {
        'total': total,
        'children': children,
        'guardians': guardians,
        'linkedChildren': linked_children,
        'unlinkedChildren': max(children - linked_children, 0),
        'totalPlayCount': total_play_count,
        'avgPlayCount': avg_play_count,
        'byRole': by_role,
        'byLang': by_lang,
    }


def list_users(page=1, page_size=20, role=None, keyword=None):
    cursor = conn.cursor()
    where_clauses = []
    params = []

    if role:
        where_clauses.append('u.role = ?')
        params.append(role)

    if keyword:
        where_clauses.append('(u.otter_id LIKE ? OR u.display_name LIKE ? OR u.email LIKE ?)')
        like_keyword = f'%{keyword}%'
        params.extend([like_keyword, like_keyword, like_keyword])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''

    cursor.execute(f'SELECT COUNT(*) FROM users u {where_sql}', params)
    total = cursor.fetchone()[0]

    offset = (page - 1) * page_size
    cursor.execute(
        f'''
        SELECT
            u.id, u.otter_id, u.role, u.display_name, u.lang, u.email,
            u.created_at, u.last_seen_at, u.status,
            COALESCE(play_counts.play_count, 0) AS play_count,
            CASE
                WHEN u.role = 'child' AND child_links.child_user_id IS NOT NULL THEN 1
                WHEN u.role = 'guardian' AND guardian_links.guardian_user_id IS NOT NULL THEN 1
                ELSE 0
            END AS linked
        FROM users u
        LEFT JOIN (
            SELECT user_id, COUNT(*) AS play_count
            FROM tracking_events
            WHERE event = 'game_start' AND user_id IS NOT NULL
            GROUP BY user_id
        ) play_counts ON play_counts.user_id = u.id
        LEFT JOIN (
            SELECT DISTINCT child_user_id FROM guardian_child_links
        ) child_links ON child_links.child_user_id = u.id
        LEFT JOIN (
            SELECT DISTINCT guardian_user_id FROM guardian_child_links
        ) guardian_links ON guardian_links.guardian_user_id = u.id
        {where_sql}
        ORDER BY u.created_at DESC, u.id DESC
        LIMIT ? OFFSET ?
        ''',
        params + [page_size, offset]
    )

    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'otterId': row[1],
            'role': row[2],
            'displayName': row[3],
            'lang': row[4],
            'email': row[5],
            'createdAt': row[6],
            'lastSeenAt': row[7],
            'status': row[8],
            'playCount': row[9],
            'linked': bool(row[10]),
        })

    return {
        'page': page,
        'pageSize': page_size,
        'total': total,
        'items': items,
    }


def link_guardian_child(guardian_otter_id, child_otter_id):
    guardian = get_user_by_otter_id(guardian_otter_id)
    child = get_user_by_otter_id(child_otter_id)
    if not guardian or guardian['role'] != 'guardian':
        raise ValueError('Guardian user not found')
    if not child or child['role'] != 'child':
        raise ValueError('Child user not found')

    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT OR IGNORE INTO guardian_child_links (guardian_user_id, child_user_id)
        VALUES (?, ?)
        ''',
        (guardian['id'], child['id'])
    )
    conn.commit()
    return {'guardian': guardian, 'child': child}


def get_retention_stats():
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM retention_submissions')
    total = cursor.fetchone()[0]

    cursor.execute('SELECT lang, COUNT(*) FROM retention_submissions GROUP BY lang')
    by_lang = [{'lang': row[0], 'count': row[1]} for row in cursor.fetchall()]

    cursor.execute('SELECT id, email, wechat, lang, source, ts, created_at FROM retention_submissions ORDER BY created_at DESC LIMIT 10')
    recent = [
        {'id': row[0], 'email': row[1], 'wechat': row[2], 'lang': row[3], 'source': row[4], 'ts': row[5], 'created_at': row[6]}
        for row in cursor.fetchall()
    ]

    return {'total': total, 'byLang': by_lang, 'recent': recent}


def list_retention_submissions(page=1, page_size=20, lang=None, source=None, keyword=None):
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if lang:
        where_clauses.append('lang = ?')
        params.append(lang)

    if source:
        where_clauses.append('source = ?')
        params.append(source)

    if keyword:
        where_clauses.append('(email LIKE ? OR wechat LIKE ?)')
        like_keyword = f'%{keyword}%'
        params.extend([like_keyword, like_keyword])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''

    cursor.execute(f'SELECT COUNT(*) FROM retention_submissions {where_sql}', params)
    total = cursor.fetchone()[0]

    offset = (page - 1) * page_size
    cursor.execute(
        f'''
        SELECT id, email, wechat, lang, source, ts, created_at
        FROM retention_submissions
        {where_sql}
        ORDER BY ts DESC, id DESC
        LIMIT ? OFFSET ?
        ''',
        params + [page_size, offset]
    )

    items = [
        {
            'id': row[0],
            'email': row[1],
            'wechat': row[2],
            'lang': row[3],
            'source': row[4],
            'ts': row[5],
            'createdAt': row[6],
        }
        for row in cursor.fetchall()
    ]

    return {
        'page': page,
        'pageSize': page_size,
        'total': total,
        'items': items,
    }
