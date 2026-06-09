import sqlite3
from pathlib import Path

DB_PATH = Path("data/bot.db")
DB_PATH.parent.mkdir(exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    item_code TEXT PRIMARY KEY,
    item_name TEXT,
    price INTEGER,
    review_average REAL,
    review_count INTEGER,
    image_url TEXT,
    affiliate_url TEXT,
    status TEXT DEFAULT 'new',
    discord_message_id TEXT,
    approved_at TEXT,
    posted_at TEXT,
    threads_post_id TEXT,
    last_seen_at TEXT
)
""")

conn.commit()
conn.close()

print("DB initialized.")
