import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import logging
from typing import Dict, List, Optional

class EcommerceScraper:
    def __init__(self, headless=True):
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Configure Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent bot detection
        
        # Initialize the Chrome WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Common e-commerce XPath patterns
        self.common_xpaths = {
            'flipkart': {
                'product_container': "//div[contains(@class, 'cPHDOP col-12-12')]",
                'product_name': ".//div[contains(@class, 'KzDlHZ')]",
                'price': ".//div[contains(@class, 'Nx9bqj _4b5DiR')]",
                # 'original_price': ".//div[contains(@class, '_3I9_wc')]",
                # 'discount': ".//div[contains(@class, '_3Ay6Sb')]",
                # 'rating': ".//div[contains(@class, '_3LWZlK')]",
                'reviews_count': ".//span[contains(@class, 'Wphh3N')]",
                'next_page': "//a[contains(@class, '_9QVEpD')]"  # Next page button
            },
            'amazon': {
                'product_container': "//div[contains(@class, 's-result-item')]",
                'product_name': ".//span[contains(@class, 'a-text-normal')]",
                'price': ".//span[contains(@class, 'a-price-whole')]",
                # 'original_price': ".//span[contains(@class, 'a-text-strike')]",
                # 'rating': ".//span[contains(@class, 'a-icon-alt')]",
                'reviews_count': ".//span[contains(@class, 'a-size-base')]",
                'next_page': "//a[contains(@class, 's-pagination-next')]"  # Next page button
            },
            # Add more websites as needed
        }
        
        self.logger.info("E-commerce scraper initialized successfully")

    def detect_website(self, url: str) -> str:
        # Detect which e-commerce website we're dealing with.
        domain_mapping = {
            'flipkart.com': 'flipkart',
            'amazon.com': 'amazon',
        }
        
        for domain, site in domain_mapping.items():
            if domain in url.lower():
                return site
        return 'generic'

    def navigate_to_page(self, url: str):
        # Navigate to a given URL and handle common popups.
        try:
            self.driver.get(url)
            self.logger.info(f"Navigated to {url}")
            
            # Handle potential popups
            time.sleep(2)
            
            # Wait for main content to load
            self.wait_for_element("//body")
        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {str(e)}")
    
    def wait_for_element(self,element, xpath: str) -> Optional[object]:
        # Wait for an element to appear on the page.
         try:
            return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
         except TimeoutException:
            self.logger.warning(f"Element not found: {xpath}")
            return None
    
    def extract_text_safely(self, element, xpath: str) -> Optional[str]:
        # Safely extract text from an element using XPath.
        try:
            found_element = element.find_element(By.XPATH, xpath)
            return found_element.text.strip() if found_element else None
        except NoSuchElementException:
            return None

    def extract_product_data(self, url: str, max_pages=2) -> List[Dict]:
        # Extract product data from e-commerce search pages
        website = self.detect_website(url)
        xpaths = self.common_xpaths.get(website, {})

        if not xpaths:
            self.logger.warning(f"No predefined XPaths for {website}. Using default patterns.")
            return []

        products = []
        current_page = 1

        while current_page <= max_pages:
            self.logger.info(f"Scraping page {current_page}...")
            self.navigate_to_page(url)

            # Extract products
            containers = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, xpaths['product_container']))
            )

            for container in containers:
                product = {}
                for field, xpath in xpaths.items():
                    if field not in ['product_container', 'next_page']:
                        product[field] = self.extract_text_safely(container, xpath)

                if product:
                    products.append(product)

            # Move to next page
            try:
                next_button = self.driver.find_element(By.XPATH, xpaths['next_page'])
                if next_button:
                    next_button.click()
                    time.sleep(3)
                    current_page += 1
                else:
                    break  # No more pages
            except NoSuchElementException:
                break  # No "Next" button found

        self.logger.info(f"Extracted {len(products)} products.")
        return products
    
    def save_to_json(self, data: List[Dict], filename: str):
        # Save data to JSON file.
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Saved {len(data)} products to {filename}")

    def save_to_csv(self, data: List[Dict], filename: str):
        # Save data to CSV file.
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        self.logger.info(f"Saved {len(data)} products to {filename}")

    def close(self):
        # Close the browser.
        self.driver.quit()
        self.logger.info("Browser closed")

# Example usage
if __name__ == "__main__":
    scraper = EcommerceScraper(headless=True)
    
    try:
        # Example URLs for different e-commerce sites
        urls = [
            "https://www.flipkart.com/search?q=laptops"
            # "https://www.amazon.com/s?k=laptops"
        ]
        
        for url in urls:
            data = scraper.extract_product_data(url, max_pages=2)

            site_name = scraper.detect_website(url)
            scraper.save_to_json(data, f"{site_name}_products.json")
            scraper.save_to_csv(data, f"{site_name}_products.csv")
            
    finally:
        scraper.close()