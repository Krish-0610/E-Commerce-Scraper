import time
import csv
import json
import re
import concurrent.futures
from functools import lru_cache
import requests
from bs4 import BeautifulSoup
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

# Global driver instance for reuse
_driver = None

def get_driver():
    """Get or create a WebDriver instance"""
    global _driver
    if _driver is None:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=service, options=chrome_options)
    return _driver

def close_driver():
    """Close the WebDriver instance when done"""
    global _driver
    if _driver:
        _driver.quit()
        _driver = None

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

    driver = get_driver()
    products = []
    
    try:
        driver.get(url)
        
        # Wait for search box to be present instead of sleeping
        search_box_xpath = SELECTORS[domain]["search_box"]
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, search_box_xpath))
        )

        # Perform search
        search_box = driver.find_element(By.XPATH, search_box_xpath)
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
        
        # Wait for results to load instead of sleeping
        product_container_xpath = SELECTORS[domain]["container"]
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, product_container_xpath))
        )

        # Extract product details
        product_elements = driver.find_elements(By.XPATH, product_container_xpath)
        
        # Use thread pool for parallel processing of product elements
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for product in product_elements:
                futures.append(
                    executor.submit(extract_product_data, product, domain)
                )
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    products.append(result)

        return products
    except Exception as e:
        print(f"Error in scrape_ecom: {e}")
        return []

def extract_product_data(product_element, domain):
    """Extract data from a product element - used for parallel processing"""
    try:
        title_xpath = SELECTORS[domain]["title"]
        price_xpath = SELECTORS[domain]["price"]
        rating_xpath = SELECTORS[domain]["rating"]
        url_xpath = SELECTORS[domain]["url"]

        title = product_element.find_element(By.XPATH, title_xpath).text
        price = product_element.find_element(By.XPATH, price_xpath).text
        
        # Try to get rating, but don't fail if not available
        try:
            rating = product_element.find_element(By.XPATH, rating_xpath).text
        except:
            rating = "N/A"
            
        url_element = product_element.find_element(By.XPATH, url_xpath)
        url = url_element.get_attribute("href")

        return [title, price, rating, url]
    except Exception as e:
        print(f"Error extracting product data: {e}")
        return None

# Cache results for 1 hour (3600 seconds)
@lru_cache(maxsize=128)
def scrape_product_cached(url, timestamp=None):
    """Cached version of scrape_product with a timestamp for cache invalidation"""
    return scrape_product_actual(url)

def scrape_product(url):
    """Wrapper that uses the cached version but invalidates cache after an hour"""
    # Round to nearest hour for cache efficiency while still refreshing hourly
    timestamp = int(time.time()) // 3600
    return scrape_product_cached(url, timestamp)

def scrape_product_actual(url):
    """Scrapes a single product, with a hybrid approach using requests+BS4 first"""
    domain = get_domain(url)
    if not domain or domain not in SELECTORS:
        print("Unsupported domain. Only Amazon and Flipkart are supported.")
        return []
    
    # Try with requests+BeautifulSoup first (faster)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract based on domain
            if domain == 'amazon':
                title = soup.select_one('#productTitle').text.strip() if soup.select_one('#productTitle') else ""
                # Try different price selectors
                price_element = soup.select_one('.a-price .a-offscreen')
                price = price_element.text.strip() if price_element else ""
                rating_element = soup.select_one('#acrPopover .a-icon-alt')
                rating = rating_element.text.strip() if rating_element else "N/A"
                
                if title and price:
                    return [[title, price, rating]]
                    
            elif domain == 'flipkart':
                title = soup.select_one('.B_NuCI').text.strip() if soup.select_one('.B_NuCI') else ""
                price_element = soup.select_one('._30jeq3')
                price = price_element.text.strip() if price_element else ""
                rating_element = soup.select_one('._2d4LTz')
                rating = rating_element.text.strip() if rating_element else "N/A"
                
                if title and price:
                    return [[title, price, rating]]
    
    except Exception as e:
        print(f"BS4 approach failed, falling back to Selenium: {e}")
    
    # Fall back to Selenium if BS4 approach failed
    driver = get_driver()
    
    try:
        driver.get(url)
        
        # Wait for the product title to be present
        title_xpath = SELECTORS[domain]["product_title"]
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, title_xpath))
        )

        # Extract product details
        title = driver.find_element(By.XPATH, title_xpath).text
        
        try:
            price_xpath = SELECTORS[domain]["product_price"]
            price = driver.find_element(By.XPATH, price_xpath).text
            if price == '' and domain == 'amazon':
                price = driver.execute_script("return document.querySelector('.a-price .a-offscreen')?.innerText;")
        except:
            price = "N/A"
            
        try:
            rating_xpath = SELECTORS[domain]["product_rating"]
            rating = driver.find_element(By.XPATH, rating_xpath).text
        except:
            rating = "N/A"

        return [[title, price, rating]]
    except Exception as e:
        print(f"Error in scrape_product: {e}")
        return []

def update_prices_batch(urls):
    """Update prices for multiple URLs in parallel"""
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(scrape_product, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
                results.append((url, data))
            except Exception as e:
                print(f"Error processing {url}: {e}")
                results.append((url, None))
    
    return results

# Make sure to call this when your application shuts down
def cleanup():
    close_driver()