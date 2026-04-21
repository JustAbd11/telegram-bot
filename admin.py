import time
from datetime import datetime, timedelta
import database as db
from config import ADMIN_IDS

def is_admin(user_id):
    return user_id in ADMIN_IDS

def activate_user(admin_id, target_user_id, days):
    """يقوم الأدمن بتفعيل مستخدم لمدة days أيام"""
    if not is_admin(admin_id):
        return False, "ليس لديك صلاحية أدمن."
    
    expires_at = datetime.now() + timedelta(days=days)
    expires_timestamp = expires_at.timestamp()
    db.add_authorized_user(target_user_id, admin_id, expires_timestamp)
    return True, f"تم تفعيل المستخدم {target_user_id} لمدة {days} يوم/أيام."

def check_user_access(user_id):
    """يتحقق إذا كان المستخدم مفعلاً ولم تنته صلاحيته"""
    return db.is_user_authorized(user_id)

def get_user_expiry(user_id):
    conn = sqlite3.connect(db.DATABASE_NAME)
    c = conn.cursor()
    c.execute('SELECT expires_at FROM authorized_users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return datetime.fromtimestamp(row[0]).strftime("%Y-%m-%d %H:%M:%S")
    return None