import sqlite3

DATABASE = "products.db"

def get_db_connection():
    """Get a connection to the database with row factory set to sqlite3.Row"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Creates necessary tables in the database if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracked_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            product_url TEXT NOT NULL,
            platform TEXT NOT NULL,
            current_price REAL NOT NULL,
            previous_price REAL,
            price_threshold REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, product_url)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database and tables initialized successfully.")

def clean_price(price_str):
    """Convert a price string to a float (removes commas and currency symbols)."""
    try:
        return float(price_str.replace(",", "").replace("₹", "").strip())  # Adjust for your currency
    except ValueError:
        return None  # Handle invalid prices gracefully

def insert_product(user_id, product_name, product_url, platform, current_price, price_threshold=None):
    """Inserts a product into the tracked_products table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if isinstance(current_price, str):
        current_price = clean_price(current_price)

    try:
        cursor.execute('''
            INSERT INTO tracked_products (user_id, product_name, product_url, platform, current_price, price_threshold)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, product_name, product_url, platform, current_price, price_threshold))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"⚠️ Product already exists for this user: {product_name}")
        return False
    finally:
        conn.close()

def get_user_tracked_products(user_id):
    """Retrieves all tracked products for a specific user from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tracked_products WHERE user_id = ?", (user_id,))
    products = cursor.fetchall()
    
    conn.close()
    return products

def delete_tracked_product(user_id, product_id):
    """Deletes a tracked product for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM tracked_products WHERE id = ? AND user_id = ?", (product_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()  # Run this file to initialize the database
