import sqlite3
import os

DB_PATH = os.path.join("data", "bot_database.db")

def init_db():
    """DB 디렉토리 및 테이블 생성 (reaction_count 컬럼 포함)"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. messages 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            channel_name TEXT,
            author_id INTEGER,
            author_name TEXT,
            content TEXT,
            reaction_count INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    
    # 2. 기존 DB 구버전 마이그레이션 (reaction_count 컬럼 누락 체크)
    cursor.execute("PRAGMA table_info(messages)")
    columns = [column[1] for column in cursor.fetchall()]
    if "reaction_count" not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN reaction_count INTEGER DEFAULT 0")
        
    conn.commit()
    conn.close()

def save_messages(messages):
    """메시지 데이터 목록 DB 저장 (중복 메시지는 무시)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR IGNORE INTO messages 
        (message_id, channel_id, channel_name, author_id, author_name, content, reaction_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, messages)
    conn.commit()
    conn.close()

def get_channel_messages(channel_id: int):
    """특정 채널 ID의 전체 메시지 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT message_id, channel_id, channel_name, author_id, author_name, content, reaction_count, created_at
        FROM messages
        WHERE channel_id = ?
    """, (channel_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows