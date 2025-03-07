import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")  # Change user agent

def scrape_amazon(search_query, max_pages=2):

    # Setup WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # Open Amazon
    url = "https://www.amazon.in/"
    driver.get(url)
    time.sleep(2)

    # Search for a product
    search_box = driver.find_element(By.ID, "twotabsearchtextbox")
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)

    time.sleep(3)  # Wait for results

    # Extract product containers

    data = []
    for i in range(1,max_pages+1):
        print("Scraping page",i,"....")
        products = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")

        for product in products:
            try:
                title = product.find_element(By.XPATH, ".//h2[@class='a-size-medium a-spacing-none a-color-base a-text-normal']").text
            except:
                print("NONE")
                title = "N/A"

            try:
                price = product.find_element(By.XPATH, ".//span[@class='a-price-whole']").text
            except:
                price = "N/A"

            try:
                rating = product.find_element(By.XPATH, ".//div[@class='a-row a-size-base']//span").text
            except:
                rating = "N/A"

            data.append([title, price, rating])
        try:
            next_button = driver.find_element(By.XPATH, "//a[contains(@class,'s-pagination-item s-pagination-next s-pagination-button s-pagination-button-accessibility s-pagination-separator')]")
            next_button.click()
            time.sleep(3)
        except:
            print("No more pages found.")
            break
    driver.quit()
    return data
