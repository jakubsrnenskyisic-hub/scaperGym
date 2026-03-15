import os
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def scrape_gym(gym_name):
    print(f"Searching for: {gym_name}")
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Nutné pro GitHub
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=cs-CZ")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        query = f"{gym_name} Praha"
        driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        time.sleep(5) # Počkáme na vykreslení grafů

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        busyness_block = soup.find("div", {"data-attrid": "kc:/local:busyness"})
        
        if busyness_block:
            match = re.search(r'(\d+)\s*%', busyness_block.get_text())
            if match:
                print(f"🏆 SUCCESS: {gym_name} is at {match.group(1)}%")
                return match.group(1)
        
        print(f"❌ No live data for {gym_name}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Testujeme jedno fitko
    scrape_gym("Form Factory Palladium")