from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urlparse

def extract_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    # Remove subdomains (like "www.")
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

def load_selectors():
    with open('selectors.json') as f:
        selectors = json.load(f)
    return selectors

def scrape_website(url):
    domain = extract_domain(url)
    selectors = load_selectors()

    if domain not in selectors:
        print(f"Selectors for {domain} not supported")
        return []
    
    site_selectors = selectors[domain]

    #Initialize the webdriver
    service = Service("C:/Users/Krish Patel/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service)

    try:
        driver.get(url)
        time.sleep(3)  # Wait for dynamic content to load
        page_source = driver.page_source
        print("Page source fetched successfully.")

    except Exception as e:
        print("Error during Selenium operation:", e)
        return []
    
    finally:
        driver.quit()

    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        scraped_data = []

        for product in soup.select(site_selectors["product_container"]):
            name = product.select_one(site_selectors["name"])
            price = product.select_one(site_selectors["price"])
            rating = product.select_one(site_selectors.get("rating", ""))

            scraped_data.append({
                "name": name.text.strip() if name else "N/A",
                "price": price.text.strip() if price else "N/A",
                "rating": rating.text.strip() if rating else "N/A",
            })
            
        return scraped_data
    except Exception as e:
        print("Error during parsing:", e)
        return []

# Example usage
if __name__ == "__main__":
    url = input("Enter the e-commerce URL to scrape: ")
    scraped_data = scrape_website(url)
    if scraped_data:
        for idx, product in enumerate(scraped_data, start=1):
            print(f"{idx}. {product['name']} - {product['price']} - {product['rating']}")
    else:
        print("No products found or an error occurred.")