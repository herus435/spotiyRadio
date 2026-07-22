import sqlite3
from datetime import datetime

DB_NAME = "radio_history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Dinleme geçmişi tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS play_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id TEXT,
            track_name TEXT,
            artist_name TEXT,
            played_at DATETIME,
            duration_ms INTEGER,
            UNIQUE(track_id, played_at)
        )
    ''')
    conn.commit()
    conn.close()

def insert_track(track_id, track_name, artist_name, played_at, duration_ms):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO play_history (track_id, track_name, artist_name, played_at, duration_ms)
            VALUES (?, ?, ?, ?, ?)
        ''', (track_id, track_name, artist_name, played_at, duration_ms))
        conn.commit()
    except Exception as e:
        print(f"DB Insert Error: {e}")
    finally:
        conn.close()