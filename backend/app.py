from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import scrape_ecom

app = Flask(__name__)
CORS(app)
@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    platform = data.get("platform")
    query = data.get("query")

    url_map = {
        "amazon": "https://www.amazon.in/",
        "flipkart": "https://www.flipkart.com/"
    }

    if platform not in url_map:
        return jsonify({"error": "Invalid platform"}), 400

    results = scrape_ecom(url_map[platform], query)
    
    response = [{"title": item[0], "price": item[1], "rating": item[2]} for item in results]
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
