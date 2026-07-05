import sqlite3
from datetime import datetime
from database.database import get_connection
import hashlib
import os

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2 and a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return salt.hex() + ":" + key.hex()

def verify_password(stored_password_hash: str, provided_password: str) -> bool:
    """Verify a provided password against a stored PBKDF2 hash."""
    try:
        salt_hex, key_hex = stored_password_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        
        actual_key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        return expected_key == actual_key
    except Exception:
        return False

def register_recruiter(fullname: str, email: str, company_name: str, password: str) -> bool:
    """Register a new recruiter in the SQLite database."""
    pw_hash = hash_password(password)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO recruiters (fullname, email, company_name, password_hash)
        VALUES (?, ?, ?, ?)
        """, (fullname, email.strip().lower(), company_name, pw_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Email already exists
    finally:
        conn.close()

def authenticate_recruiter(email: str, password: str) -> dict:
    """Authenticate a recruiter and update last login time. Returns recruiter info dict or None."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT id, fullname, email, company_name, password_hash 
        FROM recruiters 
        WHERE email = ?
        """, (email.strip().lower(),))
        row = cursor.fetchone()
        
        if row and verify_password(row["password_hash"], password):
            # Enforce email verification check
            if not is_email_verified(email):
                log_security_event("AUTHENTICATION_DENIED_UNVERIFIED", f"Email: {email.strip().lower()}")
                return None
                
            # Update last login
            now = datetime.now().isoformat()
            cursor.execute("""
            UPDATE recruiters SET last_login = ? WHERE id = ?
            """, (now, row["id"]))
            conn.commit()
            
            return {
                "id": row["id"],
                "fullname": row["fullname"],
                "email": row["email"],
                "company_name": row["company_name"]
            }
        return None
    finally:
        conn.close()

def update_password(email: str, new_password: str) -> bool:
    """Reset / update the password for a recruiter email."""
    pw_hash = hash_password(new_password)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM recruiters WHERE email = ?", (email.strip().lower(),))
        if cursor.fetchone():
            cursor.execute("UPDATE recruiters SET password_hash = ? WHERE email = ?", (pw_hash, email.strip().lower()))
            conn.commit()
            return True
        return False
    finally:
        conn.close()

def recruiter_email_exists(email: str) -> bool:
    """Check if a recruiter email exists in the system."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM recruiters WHERE email = ?", (email.strip().lower(),))
        return cursor.fetchone() is not None
    finally:
        conn.close()

def get_recruiter_details(recruiter_id: int) -> dict:
    """Retrieve full recruiter profile details from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT id, fullname, email, company_name, created_date, last_login 
        FROM recruiters 
        WHERE id = ?
        """, (recruiter_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "fullname": row["fullname"],
                "email": row["email"],
                "company_name": row["company_name"],
                "created_date": row["created_date"],
                "last_login": row["last_login"]
            }
        return None
    finally:
        conn.close()

def update_recruiter_profile(recruiter_id: int, fullname: str, company_name: str) -> bool:
    """Update a recruiter's Full Name and Company Name in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE recruiters 
        SET fullname = ?, company_name = ? 
        WHERE id = ?
        """, (fullname, company_name, recruiter_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()

def log_security_event(event_type: str, details: str):
    """Log a security event to logs/security_audit.log."""
    import os
    from datetime import datetime
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] [SECURITY_AUDIT] [{event_type}] {details}\n"
    with open("logs/security_audit.log", "a", encoding="utf-8") as f:
        f.write(log_line)
    print(f"[SECURITY_AUDIT] [{event_type}] {details}")

def create_password_reset_token(email: str) -> str:
    """Generate and store a secure password reset token for a recruiter email."""
    import secrets
    from datetime import datetime, timedelta
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM recruiters WHERE email = ?", (email.strip().lower(),))
        row = cursor.fetchone()
        
        # Log request (prevents timing details attack on validation check)
        log_security_event("PASSWORD_RESET_REQUESTED", f"Email: {email.strip().lower()}")
        
        if not row:
            # Simulate work delay to mitigate side-channel timing analysis
            secrets.token_urlsafe(32)
            hashlib.sha256(b"dummy").hexdigest()
            return None
            
        recruiter_id = row["id"]
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        now = datetime.now()
        expiry = now + timedelta(minutes=15)
        
        # Save to database
        cursor.execute("""
        INSERT INTO password_reset_tokens (recruiter_id, token_hash, created_time, expiry_time)
        VALUES (?, ?, ?, ?)
        """, (recruiter_id, token_hash, now.isoformat(), expiry.isoformat()))
        conn.commit()
        
        # Log simulated dispatch
        log_security_event("EMAIL_SENT", f"Recruiter ID: {recruiter_id}")
        
        return raw_token
    finally:
        conn.close()

def verify_password_reset_token(token: str) -> dict:
    """Validate token and return recruiter details if valid, or None."""
    if not token:
        log_security_event("INVALID_TOKEN", "Empty token provided")
        return None
        
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT t.id, t.recruiter_id, t.expiry_time, t.used, r.email 
        FROM password_reset_tokens t
        JOIN recruiters r ON t.recruiter_id = r.id
        WHERE t.token_hash = ?
        """, (token_hash,))
        row = cursor.fetchone()
        
        if not row:
            log_security_event("INVALID_TOKEN", "Token hash not found in database")
            return None
            
        if row["used"] == 1:
            log_security_event("INVALID_TOKEN", f"Token already used. Recruiter ID: {row['recruiter_id']}")
            return None
            
        # Check expiry
        expiry = datetime.fromisoformat(row["expiry_time"])
        if datetime.now() > expiry:
            log_security_event("EXPIRED_TOKEN", f"Token expired at {row['expiry_time']}. Recruiter ID: {row['recruiter_id']}")
            return None
            
        return {
            "token_id": row["id"],
            "recruiter_id": row["recruiter_id"],
            "email": row["email"]
        }
    finally:
        conn.close()

def execute_password_reset(token: str, new_password: str) -> bool:
    """Reset password and invalidate token."""
    token_details = verify_password_reset_token(token)
    if not token_details:
        return False
        
    pw_hash = hash_password(new_password)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Update recruiter password
        cursor.execute("""
        UPDATE recruiters 
        SET password_hash = ? 
        WHERE id = ?
        """, (pw_hash, token_details["recruiter_id"]))
        
        # Invalidate token immediately
        cursor.execute("""
        UPDATE password_reset_tokens 
        SET used = 1 
        WHERE id = ?
        """, (token_details["token_id"],))
        
        conn.commit()
        log_security_event("RESET_COMPLETED", f"Recruiter ID: {token_details['recruiter_id']}")
        return True
    finally:
        conn.close()

def create_email_otp(email: str) -> str:
    """Generate and store a secure 6-digit verification OTP for a recruiter email."""
    import secrets
    from datetime import datetime, timedelta
    
    # 6-digit numeric OTP
    otp = f"{secrets.randbelow(900000) + 100000:06d}"
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    
    now = datetime.now()
    expiry = now + timedelta(minutes=5)
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Invalidate any previous OTPs for this email by deleting them
        cursor.execute("DELETE FROM email_verifications WHERE email = ?", (email.strip().lower(),))
        
        # Store new OTP
        cursor.execute("""
        INSERT INTO email_verifications (email, otp_hash, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        """, (email.strip().lower(), otp_hash, now.isoformat(), expiry.isoformat()))
        conn.commit()
        
        log_security_event("OTP_GENERATED", f"Email: {email.strip().lower()}")
        return otp
    finally:
        conn.close()

def verify_email_otp(email: str, otp: str) -> bool:
    """Validate OTP and mark email as verified if correct and active."""
    if not otp:
        log_security_event("INVALID_OTP", "Empty OTP provided")
        return False
        
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT id, otp_hash, expires_at, verified 
        FROM email_verifications 
        WHERE email = ?
        """, (email.strip().lower(),))
        row = cursor.fetchone()
        
        if not row:
            log_security_event("INVALID_OTP", f"No OTP record found for: {email.strip().lower()}")
            return False
            
        if row["verified"] == 1:
            log_security_event("INVALID_OTP", f"OTP already used/verified for: {email.strip().lower()}")
            return False
            
        # Check expiry
        expiry = datetime.fromisoformat(row["expires_at"])
        if datetime.now() > expiry:
            log_security_event("EXPIRED_OTP", f"OTP expired at {row['expires_at']} for: {email.strip().lower()}")
            return False
            
        if row["otp_hash"] != otp_hash:
            log_security_event("INVALID_OTP", f"Incorrect OTP entered for: {email.strip().lower()}")
            return False
            
        # Mark as verified and invalidate immediately (verified flag = 1)
        cursor.execute("""
        UPDATE email_verifications 
        SET verified = 1 
        WHERE id = ?
        """, (row["id"],))
        conn.commit()
        
        log_security_event("OTP_VERIFIED", f"Email: {email.strip().lower()}")
        return True
    finally:
        conn.close()

def is_email_verified(email: str) -> bool:
    """Check if the email has been verified. Returns True if verified or if legacy (no verification record exists)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT verified FROM email_verifications WHERE email = ?", (email.strip().lower(),))
        row = cursor.fetchone()
        if row:
            return row["verified"] == 1
        # If no verification record exists, check if account exists (legacy support)
        cursor.execute("SELECT id FROM recruiters WHERE email = ?", (email.strip().lower(),))
        return cursor.fetchone() is not None
    finally:
        conn.close()
