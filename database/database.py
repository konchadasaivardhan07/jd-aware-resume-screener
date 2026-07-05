import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "hiresense.db"

def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database schema if not already present."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create recruiters table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recruiters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        company_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    """)
    
    # Create password_reset_tokens table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recruiter_id INTEGER NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        created_time TIMESTAMP NOT NULL,
        expiry_time TIMESTAMP NOT NULL,
        used INTEGER DEFAULT 0,
        FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
    )
    """)
    
    # Create email_verifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        otp_hash TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        verified INTEGER DEFAULT 0
    )
    """)
    
    conn.commit()
    conn.close()

# Initialize on import
init_db()
