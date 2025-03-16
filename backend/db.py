import sqlite3

DATABASE = "products.db"

def create_tables():
    """Creates necessary tables in the database if they do not exist."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracked_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_url TEXT UNIQUE NOT NULL,
            platform TEXT NOT NULL,
            current_price REAL NOT NULL,
            previous_price REAL,
            price_threshold REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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


def insert_product(product_name, product_url, current_price):
    """Inserts a product into the tracked_products table."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cleaned_price = clean_price(current_price)

    try:
        cursor.execute('''
            INSERT INTO tracked_products (product_name, product_url, current_price)
            VALUES (?, ?, ?)
        ''', (product_name, product_url, cleaned_price))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"⚠️ Product already exists: {product_name}")
    
    conn.close()

def get_all_tracked_products():
    """Retrieves all tracked products from the database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tracked_products")
    products = cursor.fetchall()
    
    conn.close()
    return products

if __name__ == "__main__":
    create_tables()  # Run this file to initialize the database
