import sqlite3
import os

DB_PATH = "data/bot_database.db"

def init_db():
    """데이터베이스 및 테이블 초기화"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 메시지 저장 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            channel_name TEXT,
            author_id INTEGER,
            author_name TEXT,
            content TEXT,
            reactions_count INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_messages(messages_list):
    """수집된 메시지 리스트를 DB에 INSERT OR REPLACE (중복 자동 방지)"""
    if not messages_list:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.executemany("""
        INSERT OR REPLACE INTO messages 
        (message_id, channel_id, channel_name, author_id, author_name, content, reactions_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, messages_list)
    
    conn.commit()
    conn.close()

def get_channel_messages(channel_name: str):
    """특정 채널의 메시지 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT message_id, channel_id, channel_name, author_id, author_name, content, reactions_count, created_at
        FROM messages
        WHERE channel_name = ?
        ORDER BY created_at ASC
    """, (channel_name,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows