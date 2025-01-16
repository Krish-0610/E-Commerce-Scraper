import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
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
        chrome_options.add_argument('--disable-notifications')  # Block notifications
        chrome_options.add_argument('--disable-popup-blocking')  # Handle popups
        
        # Initialize the Chrome WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Common e-commerce XPath patterns
        self.common_xpaths = {
            'flipkart': {
                'product_container': "//div[contains(@class, '_1AtVbE')]",
                'product_name': ".//a[contains(@class, 's1Q9rs')]",
                'price': ".//div[contains(@class, '_30jeq3')]",
                'original_price': ".//div[contains(@class, '_3I9_wc')]",
                'discount': ".//div[contains(@class, '_3Ay6Sb')]",
                'rating': ".//div[contains(@class, '_3LWZlK')]",
                'reviews_count': ".//span[contains(@class, '_2_R_DZ')]"
            },
            'amazon': {
                'product_container': "//div[contains(@class, 's-result-item')]",
                'product_name': ".//span[contains(@class, 'a-text-normal')]",
                'price': ".//span[contains(@class, 'a-price-whole')]",
                'original_price': ".//span[contains(@class, 'a-text-strike')]",
                'rating': ".//span[contains(@class, 'a-icon-alt')]",
                'reviews_count': ".//span[contains(@class, 'a-size-base')]"
            },
            # Add more websites as needed
        }
        
        self.logger.info("E-commerce scraper initialized successfully")

    def detect_website(self, url: str) -> str:
        """Detect which e-commerce website we're dealing with."""
        domain_mapping = {
            'flipkart.com': 'flipkart',
            'amazon.com': 'amazon',
            # Add more mappings as needed
        }
        
        for domain, site in domain_mapping.items():
            if domain in url.lower():
                return site
        return 'generic'

    def handle_popup(self):
        """Handle common e-commerce popup patterns."""
        common_popup_patterns = [
            "//button[contains(@class, 'close')]",
            "//button[contains(@class, 'popup-close')]",
            "//div[contains(@class, 'modal')]//button",
            "//button[contains(text(), 'No thanks')]",
            "//button[contains(text(), 'Close')]"
        ]
        
        for pattern in common_popup_patterns:
            try:
                popup = self.driver.find_element(By.XPATH, pattern)
                popup.click()
                self.logger.info("Popup handled successfully")
                break
            except NoSuchElementException:
                continue

    def navigate_to_page(self, url: str):
        try:
            self.driver.get(url)
            self.logger.info(f"Navigated to {url}")
            
            # Handle potential popups
            time.sleep(2)
            self.handle_popup()
            
            # Wait for main content to load
            self.wait_for_element("//body")
            time.sleep(2)
        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {str(e)}")
            raise

    def wait_for_element(self, xpath: str) -> Optional[object]:
        try:
            element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element
        except TimeoutException:
            self.logger.error(f"Timeout waiting for element: {xpath}")
            return None

    def extract_text_safely(self, element, xpath: str) -> Optional[str]:
        """Safely extract text from an element using relative XPath."""
        try:
            found_element = element.find_element(By.XPATH, xpath)
            return found_element.text.strip()
        except (NoSuchElementException, AttributeError):
            return None

    def extract_product_data(self, url: str) -> List[Dict]:
        """Extract product data using website-specific XPaths."""
        website = self.detect_website(url)
        xpaths = self.common_xpaths.get(website, {})
        
        if not xpaths:
            self.logger.warning(f"No predefined XPaths for {website}. Using generic patterns.")
            xpaths = {
                'product_container': "//div[contains(@class, 'product') or contains(@class, 'item')]",
                'product_name': ".//h2|.//h3|.//a[contains(@class, 'title')]",
                'price': ".//span[contains(@class, 'price')]|.//div[contains(@class, 'price')]",
                'rating': ".//div[contains(@class, 'rating')]|.//span[contains(@class, 'rating')]"
            }

        try:
            # Wait for product containers to load
            containers = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, xpaths['product_container'])
                )
            )
            
            products = []
            for container in containers:
                product = {}
                
                # Extract each field using relative XPaths
                for field, xpath in xpaths.items():
                    if field != 'product_container':
                        value = self.extract_text_safely(container, xpath)
                        if value:
                            product[field] = value
                
                if product:  # Only add if we found any data
                    products.append(product)
                    
            self.logger.info(f"Extracted {len(products)} products")
            return products
            
        except Exception as e:
            self.logger.error(f"Error during data extraction: {str(e)}")
            return []

    def scroll_page(self, scroll_pause=1.0, max_scrolls=None):
        """Scroll the page to load dynamic content."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        
        while True:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            
            # Handle any popups that might appear during scrolling
            self.handle_popup()
            
            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count += 1
            
            if new_height == last_height or (max_scrolls and scroll_count >= max_scrolls):
                break
            last_height = new_height
            
        self.logger.info(f"Completed page scrolling after {scroll_count} scrolls")

    def save_to_json(self, data: List[Dict], filename: str, pretty: bool = True):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(data)} products to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            raise

    def save_to_csv(self, data: List[Dict], filename: str):
        try:
            df = pd.DataFrame(data)
            df = df.replace(r'^\s*$', None, regex=True)
            df.to_csv(filename, index=False, na_rep='N/A')
            
            # Log data quality statistics
            self.logger.info("Data quality report:")
            for column in df.columns:
                missing = df[column].isna().sum()
                total = len(df)
                self.logger.info(f"{column}: {total-missing}/{total} values present ({missing} missing)")
                
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            raise

    def close(self):
        """Clean up resources."""
        self.driver.quit()
        self.logger.info("Browser closed")

# Example usage
if __name__ == "__main__":
    scraper = EcommerceScraper(headless=True)
    
    try:
        # Example URLs for different e-commerce sites
        urls = [
            "https://www.flipkart.com/search?q=laptops",
            "https://www.amazon.com/s?k=laptops"
        ]
        
        for url in urls:
            scraper.navigate_to_page(url)
            scraper.scroll_page(max_scrolls=3)  # Limit scrolling for testing
            data = scraper.extract_product_data(url)
            
            # Save data
            site_name = scraper.detect_website(url)
            scraper.save_to_json(data, f"{site_name}_products.json")
            scraper.save_to_csv(data, f"{site_name}_products.csv")
            
    finally:
        scraper.close()