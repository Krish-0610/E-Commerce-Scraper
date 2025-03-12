import pandas as pd
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from scraper import scrape_ecom

app = Flask(__name__)
CORS(app)

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
    
    response = [{"title": item[0], "price": item[1], "rating": item[2]} for item in scraped_data]
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

if __name__ == '__main__':
    app.run(debug=True)
