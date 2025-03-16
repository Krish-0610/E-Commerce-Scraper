import pandas as pd
import os
import sqlite3
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from scraper import scrape_ecom, scrape_product, get_domain


app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect("products.db")
    conn.row_factory = sqlite3.Row
    return conn

scraped_data = []
@app.route('/scrape', methods=['POST'])
def scrape():
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
        df.to_csv(filepath, index=False, header=["Title", "Price", "Rating"])
        mime_type = "text/csv"
    elif file_format == "json":
        df.to_json(filepath, orient="records", lines=True)
        mime_type = "application/json"
    else:
        return jsonify({"error": "Invalid format"}), 400

    return send_file(filepath, mimetype=mime_type, as_attachment=True)

@app.route("/track", methods=["POST"])
def track_product():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    product_url = data.get("product_url")
    price_threshold = data.get("price_threshold", None)  # Optional threshold

    # Scrape initial price
    scraped_data = scrape_product(product_url)
    if not scraped_data:
        return jsonify({"error": "Failed to scrape product data"}), 400

    if not scraped_data:
        return jsonify({"error": "Failed to scrape product data"}), 400
    
    # Extract price from first product in the list
    current_price = scraped_data[0][1] if scraped_data else None
    product_name = scraped_data[0][0] if scraped_data else None
    platform = get_domain(product_url)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO tracked_products (product_name, platform, product_url, current_price, price_threshold)
        VALUES (?, ?, ?, ?, ?)
    ''', (product_name, platform, product_url, current_price, price_threshold))
    conn.commit()
    conn.close()

    return jsonify({"message": "Product added for tracking!", "current_price": current_price})


@app.route("/tracked_products", methods=["GET"])
def get_tracked_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tracked_products")
    products = cursor.fetchall()
    conn.close()

    product_list = [dict(row) for row in products]
    return jsonify(product_list)

@app.route("/update_prices", methods=["POST"])
def update_prices():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_url FROM tracked_products")
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
                WHERE product_url = ?
            ''', (new_price, url))

    conn.commit()
    conn.close()

    return jsonify({"message": "Prices updated successfully!"})


if __name__ == '__main__':
    app.run(debug=True)
