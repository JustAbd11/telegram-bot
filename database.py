import aiosqlite
import logging
from datetime import datetime

DB_PATH = "bot_data.db"
logger = logging.getLogger(__name__)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TEXT,
                is_blocked INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS force_sub (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE,
                channel_username TEXT,
                channel_title TEXT,
                added_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS force_sub_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_id TEXT,
                joined_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT,
                sent_at TEXT,
                total_sent INTEGER DEFAULT 0
            )
        """)
        await db.commit()
    logger.info("✅ قاعدة البيانات جاهزة")

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, full_name, joined_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, full_name, datetime.now().isoformat()))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_blocked = 0") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_user_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]

async def get_today_users():
    today = datetime.now().date().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE joined_at LIKE ?", (f"{today}%",)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0]

async def block_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def unblock_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked = 0 WHERE user_id = ?", (user_id,))
        await db.commit()

# ---- Force Subscribe ----
async def add_force_sub(channel_id: str, channel_username: str, channel_title: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO force_sub (channel_id, channel_username, channel_title, added_at)
            VALUES (?, ?, ?, ?)
        """, (channel_id, channel_username, channel_title, datetime.now().isoformat()))
        await db.commit()

async def remove_force_sub(channel_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM force_sub WHERE channel_id = ?", (channel_id,))
        await db.commit()

async def get_force_subs():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT channel_id, channel_username, channel_title FROM force_sub") as cursor:
            return await cursor.fetchall()

async def record_force_sub_join(user_id: int, channel_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        existing = await db.execute(
            "SELECT id FROM force_sub_stats WHERE user_id = ? AND channel_id = ?",
            (user_id, channel_id)
        )
        row = await existing.fetchone()
        if not row:
            await db.execute("""
                INSERT INTO force_sub_stats (user_id, channel_id, joined_at)
                VALUES (?, ?, ?)
            """, (user_id, channel_id, datetime.now().isoformat()))
            await db.commit()

async def get_force_sub_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT f.channel_title, COUNT(s.id) as count
            FROM force_sub f
            LEFT JOIN force_sub_stats s ON f.channel_id = s.channel_id
            GROUP BY f.channel_id
        """) as cursor:
            return await cursor.fetchall()
