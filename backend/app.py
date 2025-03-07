from flask import Flask, request, jsonify
from scraper import scrape_amazon
app = Flask(__name__)

@app.route("/scrape", methods=["GET"])
def scrape():
    """API Endpoint to scrape Amazon"""
    query = request.args.get("query")  # Get query from URL parameter
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    data = scrape_amazon(query, max_pages=2)  # Scrape 2 pages
    return jsonify({"query": query, "results": data})

if __name__ == "__main__":
    app.run(debug=True)
