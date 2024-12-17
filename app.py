from flask import Flask, request, render_template, redirect, url_for
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def extract_headings(soup):
    return {
        'h1': [h.text.strip() for h in soup.find_all('h1')],
        'h2': [h.text.strip() for h in soup.find_all('h2')],
        'h3': [h.text.strip() for h in soup.find_all('h3')],
    }

def extract_images(soup):
    return [img['src'] for img in soup.find_all('img') if 'src' in img.attrs]

def extract_paragraphs(soup):
    return [p.text.strip() for p in soup.find_all('p')]

def extract_links_with_keyword(soup, keyword):
    return [a['href'] for a in soup.find_all('a', href=True) if keyword in a['href']]

def scrape_website(url, filters=None):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        data = {}
        if not filters or 'links' in filters:
            data['links'] = [a['href'] for a in soup.find_all('a', href=True)]
        if 'headings' in filters:
            data['headings'] = extract_headings(soup)
        if 'images' in filters:
            data['images'] = extract_images(soup)
        if 'paragraphs' in filters:
            data['paragraphs'] = extract_paragraphs(soup)
        if 'keyword' in filters:
            keyword = filters.get('keyword', '')
            data['keyword_links'] = extract_links_with_keyword(soup, keyword)

        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        filters = request.form.getlist("filter")
        keyword = request.form.get("keyword")

        filter_dict = {filter_type: True for filter_type in filters}
        if keyword:
            filter_dict['keyword'] = keyword

        if url:
            data = scrape_website(url, filter_dict)
            return render_template("results.html", data=data, url=url)
        else:
            return redirect(url_for("index"))
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
