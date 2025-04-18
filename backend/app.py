import pandas as pd
import os
import sqlite3
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from scraper import scrape_ecom, scrape_product, get_domain
from user import login_user, register_user, verify_token, init_db as init_user_db
from db import insert_product, get_user_tracked_products, delete_tracked_product, create_tables as init_products_db
from functools import wraps

app = Flask(__name__)
CORS(app)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        print(f"Authorization header: {token}")
        
        if not token:
            print("No token provided")
            return jsonify({"error": "Token is missing"}), 401
            
        try:
            # Check if token has 'Bearer ' prefix
            if ' ' in token:
                prefix, token = token.split(' ', 1)
                print(f"Token prefix: {prefix}, Token: {token}")
                if prefix.lower() != 'bearer':
                    print(f"Invalid token prefix: {prefix}")
                    return jsonify({"error": "Invalid token format"}), 401
            
            print(f"Processing token: {token[:10]}...")
            success, payload = verify_token(token)
            
            if not success:
                print(f"Token verification failed: {payload}")
                return jsonify({"error": payload}), 401
                
            print(f"Token verified successfully for user_id: {payload.get('user_id')}")
            # Pass user_id to the wrapped function
            kwargs['user_id'] = payload['user_id']
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Token exception: {str(e)}")
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
    return decorated

def get_db_connection():
    conn = sqlite3.connect("products.db")
    conn.row_factory = sqlite3.Row
    return conn

# Authentication routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    success, message = register_user(
        data.get('name'),
        data.get('email'),
        data.get('password')
    )
    
    if success:
        return jsonify({"message": message}), 201
    return jsonify({"error": message}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    success, result = login_user(
        data.get('email'),
        data.get('password')
    )
    
    if success:
        return jsonify(result), 200
    return jsonify({"error": result}), 401

scraped_data = []
@app.route('/scrape', methods=['POST'])
@token_required
def scrape(user_id):
    global scraped_data
    data = request.json
    platform = data.get("platform")
    query = data.get("query")

    url_map = {
        "amazon": "https://www.amazon.in/",
        "flipkart": "https://www.flipkart.com/"
    }

    if platform not in url_map:
        return jsonify({"error": "Invalid platform"}), 400

    scraped_data = scrape_ecom(url_map[platform], query)
    
    response = [{"title": item[0], "price": item[1], "rating": item[2], "url": item[3]} for item in scraped_data]
    return jsonify(response)

@app.route("/download", methods=["GET"])
@token_required
def download():
    global scraped_data
    file_format = request.args.get("format", "csv").lower()

    if not scraped_data:
        return jsonify({"error": "No data available"}), 400

    df = pd.DataFrame(scraped_data)
    filename = f"scraped_data.{file_format}"
    filepath = os.path.join(os.getcwd(), filename)

    # Save the file in the correct format
    if file_format == "csv":
        df.to_csv(filepath, index=False, header=["Title", "Price", "Rating", "Url"])
        mime_type = "text/csv"
    elif file_format == "json":
        df.to_json(filepath, orient="records", lines=True)
        mime_type = "application/json"
    else:
        return jsonify({"error": "Invalid format"}), 400

    return send_file(filepath, mimetype=mime_type, as_attachment=True)

@app.route("/track", methods=["POST"])
@token_required
def track_product(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    product_url = data.get("product_url")
    price_threshold = data.get("price_threshold", None)  # Optional threshold

    # Scrape initial price
    scraped_data = scrape_product(product_url)
    if not scraped_data:
        return jsonify({"error": "Failed to scrape product data"}), 400
    
    # Extract price from first product in the list
    current_price = scraped_data[0][1] if scraped_data else None
    product_name = scraped_data[0][0] if scraped_data else None
    platform = get_domain(product_url)

    # Insert product with user_id
    success = insert_product(user_id, product_name, product_url, platform, current_price, price_threshold)
    if not success:
        return jsonify({"error": "Product already being tracked"}), 400

    return jsonify({"message": "Product added for tracking!", "current_price": current_price})

@app.route("/tracked_products", methods=["GET"])
@token_required
def get_tracked_products(user_id):
    products = get_user_tracked_products(user_id)
    product_list = [dict(row) for row in products]
    return jsonify(product_list)

@app.route("/update_prices", methods=["POST"])
@token_required
def update_prices(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_url FROM tracked_products WHERE user_id = ?", (user_id,))
    products = cursor.fetchall()

    for product in products:
        url = product["product_url"]
        scraped_data = scrape_product(url)
        if scraped_data:
            new_price = scraped_data[0][1] if scraped_data else None
            cursor.execute('''
                UPDATE tracked_products
                SET previous_price = current_price, 
                    current_price = ?, 
                    last_updated = CURRENT_TIMESTAMP
                WHERE product_url = ? AND user_id = ?
            ''', (new_price, url, user_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Prices updated successfully!"})

@app.route("/remove_tracked_product/<int:product_id>", methods=["DELETE"])
@token_required
def remove_tracked_product(product_id, user_id):
    success = delete_tracked_product(user_id, product_id)
    if not success:
        return jsonify({"error": "Product not found"}), 404
            
    return jsonify({"message": "Product removed successfully"}), 200

@app.route("/check-auth", methods=["GET"])
@token_required
def check_auth(user_id):
    """Debug endpoint to check if token authentication is working."""
    print(f"Auth check successful for user_id: {user_id}")
    return jsonify({
        "message": "Authentication successful",
        "user_id": user_id
    })

if __name__ == '__main__':
    init_user_db()
    init_products_db()
    app.run(debug=True)
