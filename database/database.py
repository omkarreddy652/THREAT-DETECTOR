import sqlite3
import hashlib
import os
import json
from datetime import datetime
import uuid

class Database:
    def __init__(self, db_path="cyberwatch.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                profile_picture TEXT,
                google_id TEXT,
                github_id TEXT,
                preferences TEXT
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User activity log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_type TEXT NOT NULL,
                description TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Scan history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                scan_type TEXT NOT NULL,
                content TEXT,
                result TEXT NOT NULL,
                confidence REAL,
                emotion TEXT,
                duration REAL,
                transcription TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password, salt=None):
        """Hash password with salt"""
        if salt is None:
            salt = os.urandom(32).hex()
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash.hex(), salt
    
    def verify_password(self, password, password_hash, salt):
        """Verify password against stored hash"""
        test_hash, _ = self.hash_password(password, salt)
        return test_hash == password_hash
    
    def register_user(self, username, email, password):
        """Register a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                return False, "Username or email already exists"
            
            # Hash password
            password_hash, salt = self.hash_password(password)
            
            # Insert new user
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, salt))
            
            user_id = cursor.lastrowid
            
            # Log activity
            cursor.execute('''
                INSERT INTO user_activity (user_id, activity_type, description)
                VALUES (?, ?, ?)
            ''', (user_id, 'REGISTER', f'User {username} registered'))
            
            conn.commit()
            conn.close()
            
            return True, "Registration successful"
            
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def authenticate_user(self, username_or_email, password):
        """Authenticate user with username/email and password"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find user by username or email
            cursor.execute("SELECT id, username, email, password_hash, salt FROM users WHERE username = ? OR email = ?", 
                         (username_or_email, username_or_email))
            user = cursor.fetchone()
            
            if not user:
                return False, "User not found"
            
            user_id, username, email, password_hash, salt = user
            
            # Verify password
            if not self.verify_password(password, password_hash, salt):
                return False, "Invalid password"
            
            # Update last login
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
            
            # Log activity
            cursor.execute('''
                INSERT INTO user_activity (user_id, activity_type, description)
                VALUES (?, ?, ?)
            ''', (user_id, 'LOGIN', f'User {username} logged in'))
            
            conn.commit()
            conn.close()
            
            return True, {
                'user_id': user_id,
                'username': username,
                'email': email
            }
            
        except Exception as e:
            return False, f"Authentication failed: {str(e)}"
    
    def create_session(self, user_id):
        """Create a new session for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate session token
            session_token = str(uuid.uuid4())
            
            # Set expiration (24 hours from now)
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(hours=24)
            
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, session_token, expires_at))
            
            conn.commit()
            conn.close()
            
            return session_token
            
        except Exception as e:
            return None
    
    def validate_session(self, session_token):
        """Validate session token and return user info"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, u.email, us.expires_at
                FROM users u
                JOIN user_sessions us ON u.id = us.user_id
                WHERE us.session_token = ? AND us.expires_at > CURRENT_TIMESTAMP
            ''', (session_token,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return True, {
                    'user_id': user[0],
                    'username': user[1],
                    'email': user[2]
                }
            else:
                return False, "Invalid or expired session"
                
        except Exception as e:
            return False, f"Session validation failed: {str(e)}"
    
    def logout_user(self, session_token):
        """Logout user by removing session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            return False
    
    def save_scan_result(self, user_id, scan_type, content, result, confidence=None, emotion=None, duration=None, transcription=None):
        """Save scan result to database with emotion, duration, transcription"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scan_history (user_id, scan_type, content, result, confidence, emotion, duration, transcription)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, scan_type, content, result, confidence, emotion, duration, transcription))
            conn.commit()
            conn.close()
            print(f"DB: Saved scan result: user_id={user_id}, scan_type={scan_type}, content={content}, result={result}, confidence={confidence}, emotion={emotion}, duration={duration}, transcription={transcription}")
            return True
        except Exception as e:
            print(f"DB save_scan_result error: {e}")
            return False

    def drop_and_recreate_scan_history(self):
        """Drop and recreate scan_history table with the correct schema (for development/testing)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS scan_history')
            conn.commit()
            conn.close()
            print("DB: Dropped scan_history table.")
            self.init_database()
            print("DB: Recreated scan_history table with new schema.")
        except Exception as e:
            print(f"DB drop_and_recreate_scan_history error: {e}")

    def get_user_scan_history(self, user_id, limit=50):
        """Get user's scan history with emotion, duration, transcription"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT scan_type, content, result, confidence, emotion, duration, transcription, timestamp
                FROM scan_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            history = cursor.fetchall()
            conn.close()
            return history
        except Exception as e:
            print(f"DB get_user_scan_history error: {e}")
            return [] 