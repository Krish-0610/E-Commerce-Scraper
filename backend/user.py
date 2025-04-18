import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta
import os

SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Use environment variable in production

def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def register_user(name, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return False, "Email already registered"
    
    # Hash password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_password.decode('utf-8'))
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return True, {"message": "Registration successful", "user_id": user_id}
    except Exception as e:
        conn.close()
        return False, str(e)

def login_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return False, "User not found"
    
    # Verify password
    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return False, "Invalid password"
    
    # Set expiration time
    exp_time = datetime.utcnow() + timedelta(days=1)
    
    # Generate JWT token
    token_payload = {
        'user_id': user['id'],
        'email': user['email'],
        'name': user['name'],
        'exp': exp_time
    }
    
    try:
        token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')
        print(f"Generated token (first 10 chars): {token[:10]}...")
        
        # Testing token verification
        test_success, test_payload = verify_token(token)
        if not test_success:
            print(f"WARNING: Generated token fails verification: {test_payload}")
        else:
            print(f"Token verification successful")
            
        return True, {
            "token": token,
            "user": {
                "id": user['id'],
                "name": user['name'],
                "email": user['email']
            }
        }
    except Exception as e:
        print(f"Error generating token: {str(e)}")
        return False, f"Authentication error: {str(e)}"

def verify_token(token):
    try:
        print(f"Attempting to decode token (first 10 chars): {token[:10]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        # Verify required claims are present
        if 'user_id' not in payload:
            print(f"Token missing required claim 'user_id': {payload}")
            return False, "Invalid token: missing user_id claim"
            
        print(f"Token successfully decoded for user_id: {payload['user_id']}")
        return True, payload
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return False, "Token has expired"
    except jwt.InvalidTokenError as e:
        print(f"Invalid token error: {str(e)}")
        return False, f"Invalid token: {str(e)}"
    except Exception as e:
        print(f"Unexpected error in token verification: {str(e)}")
        return False, f"Token verification failed: {str(e)}"

def get_user_by_id(user_id):
    """Get user details by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return None
    return dict(user)

def update_user_profile(user_id, name=None, email=None, password=None):
    """Update user profile information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        if email:
            updates.append("email = ?")
            params.append(email)
        if password:
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
            updates.append("password = ?")
            params.append(hashed_password.decode('utf-8'))
        
        if not updates:
            return False, "No updates provided"
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        return True, "Profile updated successfully"
    except sqlite3.IntegrityError:
        return False, "Email already exists"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_user(user_id):
    """Delete a user and all their tracked products"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Delete user's tracked products first (due to foreign key constraint)
        cursor.execute("DELETE FROM tracked_products WHERE user_id = ?", (user_id,))
        # Delete the user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()