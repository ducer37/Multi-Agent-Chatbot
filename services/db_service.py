import os
import json
import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv("POSTGRES_URI")

def init_db():
    if not DB_URI:
        print("⚠️ Chưa cấu hình POSTGRES_URI trong .env")
        return
        
    try:
        with psycopg.connect(DB_URI) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(255) PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS user_google_tokens (
                    user_id VARCHAR(255) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    token TEXT NOT NULL,
                    refresh_token TEXT,
                    token_uri TEXT,
                    client_id TEXT,
                    client_secret TEXT,
                    scopes TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                conn.commit()
                print("✅ Khởi tạo các bảng Database cho Users và Tokens thành công!")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo DB: {e}")

def save_user_token(user_id: str, creds_dict: dict):
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            # Ensure user exists
            cur.execute("INSERT INTO users (id) VALUES (%s) ON CONFLICT (id) DO NOTHING", (user_id,))
            
            # Save token
            cur.execute("""
            INSERT INTO user_google_tokens (user_id, token, refresh_token, token_uri, client_id, client_secret, scopes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                token = EXCLUDED.token,
                refresh_token = COALESCE(EXCLUDED.refresh_token, user_google_tokens.refresh_token),
                token_uri = EXCLUDED.token_uri,
                client_id = EXCLUDED.client_id,
                client_secret = EXCLUDED.client_secret,
                scopes = EXCLUDED.scopes,
                updated_at = CURRENT_TIMESTAMP;
            """, (
                user_id,
                creds_dict.get('token'),
                creds_dict.get('refresh_token'),
                creds_dict.get('token_uri'),
                creds_dict.get('client_id'),
                creds_dict.get('client_secret'),
                json.dumps(creds_dict.get('scopes', []))
            ))
            conn.commit()

def get_user_token(user_id: str) -> dict:
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT token, refresh_token, token_uri, client_id, client_secret, scopes FROM user_google_tokens WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                return {
                    'token': row[0],
                    'refresh_token': row[1],
                    'token_uri': row[2],
                    'client_id': row[3],
                    'client_secret': row[4],
                    'scopes': json.loads(row[5]) if row[5] else []
                }
            return None
