import sqlite3
from config import DATABASE_NAME

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    
    # جدول المستخدمين المصرح لهم باستخدام البوت
    c.execute('''
        CREATE TABLE IF NOT EXISTS authorized_users (
            user_id INTEGER PRIMARY KEY,
            activated_by INTEGER,
            activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')
    
    # جدول الحسابات (أرقام التلجرام المسجلة)
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,   -- المستخدم الذي أضاف هذا الحساب
            phone TEXT UNIQUE,
            session_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES authorized_users(user_id)
        )
    ''')
    
    # جدول المجموعات لكل حساب
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            group_id INTEGER,
            group_title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(account_id) REFERENCES accounts(id),
            UNIQUE(account_id, group_id)
        )
    ''')
    
    # جدول الإعدادات العامة
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# دوال المستخدمين المصرح لهم
def add_authorized_user(user_id, admin_id, expires_at_timestamp):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO authorized_users (user_id, activated_by, expires_at)
        VALUES (?, ?, ?)
    ''', (user_id, admin_id, expires_at_timestamp))
    conn.commit()
    conn.close()

def is_user_authorized(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT expires_at FROM authorized_users WHERE user_id = ?
    ''', (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    expires_at = row[0]
    if expires_at and expires_at < datetime.now().timestamp():
        return False
    return True

def get_all_authorized_users():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id, expires_at FROM authorized_users')
    rows = c.fetchall()
    conn.close()
    return rows

# دوال الحسابات (مع ربطها بـ user_id)
def add_account(user_id, phone, session_name):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO accounts (user_id, phone, session_name) 
        VALUES (?, ?, ?)
    ''', (user_id, phone, session_name))
    conn.commit()
    conn.close()

def get_accounts_by_user(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('SELECT id, phone, session_name FROM accounts WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "phone": r[1], "session_name": r[2]} for r in rows]

def delete_account(account_id, user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM accounts WHERE id = ? AND user_id = ?', (account_id, user_id))
    c.execute('DELETE FROM groups WHERE account_id = ?', (account_id,))
    conn.commit()
    conn.close()

def add_group(account_id, group_id, group_title):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO groups (account_id, group_id, group_title) 
        VALUES (?, ?, ?)
    ''', (account_id, group_id, group_title))
    conn.commit()
    conn.close()

def get_groups_by_account(account_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('SELECT group_id, group_title FROM groups WHERE account_id = ?', (account_id,))
    rows = c.fetchall()
    conn.close()
    return [{"group_id": r[0], "title": r[1]} for r in rows]

def clear_groups(account_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM groups WHERE account_id = ?', (account_id,))
    conn.commit()
    conn.close()

# إضافة دالة مساعدة للتاريخ
from datetime import datetime