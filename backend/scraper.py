import time
import csv
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse

# Load selectors from JSON
with open("selectors.json", "r") as f:
    SELECTORS = json.load(f)

def get_domain(url):
    """Returns the e-commerce domain (amazon, flipkart) based on the URL."""
    parsed_url = urlparse(url).netloc
    if "amazon" in parsed_url:
        return "amazon"
    elif "flipkart" in parsed_url:
        return "flipkart"
    else:
        return None

def scrape_ecom(url, search_query):
    """Scrapes product details from Amazon or Flipkart based on the URL."""
    domain = get_domain(url)
    if not domain or domain not in SELECTORS:
        print("Unsupported domain. Only Amazon and Flipkart are supported.")
        return []

    # Set up Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(2)

        # Use selectors from JSON
        search_box_xpath = SELECTORS[domain]["search_box"]
        product_container_xpath = SELECTORS[domain]["container"]
        title_xpath = SELECTORS[domain]["title"]
        price_xpath = SELECTORS[domain]["price"]
        rating_xpath = SELECTORS[domain]["rating"]
        url_xpath = SELECTORS[domain]["url"]

        # Perform search
        search_box = driver.find_element(By.XPATH, search_box_xpath)
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)

        # Extract product details
        products = []
        product_elements = driver.find_elements(By.XPATH, product_container_xpath)

        for product in product_elements:  # Limit results
            try:
                title = product.find_element(By.XPATH, title_xpath).text
                price = product.find_element(By.XPATH, price_xpath).text
                rating = product.find_element(By.XPATH, rating_xpath).text
                url_element = product.find_element(By.XPATH, url_xpath)
                url = url_element.get_attribute("href")

                products.append([title, price, rating, url])

            except Exception as e:
                print(f"Skipping a product due to error: {e}")

        return products

    finally:
        driver.quit()


def scrape_product(url):
    """Scrapes product details from Amazon or Flipkart based on the URL."""
    domain = get_domain(url)
    if not domain or domain not in SELECTORS:
        print("Unsupported domain. Only Amazon and Flipkart are supported.")
        return []

    # Set up Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(5)
       

        # Use selectors from JSON
        title_xpath = SELECTORS[domain]["product_title"]
        price_xpath = SELECTORS[domain]["product_price"]
        rating_xpath = SELECTORS[domain]["product_rating"]

        # Extract product details
        product = []

        try:
            title = driver.find_element(By.XPATH, title_xpath).text
            price = driver.find_element(By.XPATH, price_xpath).text
            if price == '' and domain == 'amazon':
                price = driver.execute_script("return document.querySelector('.a-price .a-offscreen')?.innerText;")
            rating = driver.find_element(By.XPATH, rating_xpath).text

            product.append([title, price, rating])

        except Exception as e:
                print(f"Skipping a product due to error: {e}")

        return product

    finally:
        driver.quit()