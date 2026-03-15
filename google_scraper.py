import os
import time
import re
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def scrape_gyms(gym_list):
    results = {}
    
    # Pokud už soubor existuje, načteme stará data, abychom je nepřepsali
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            results = json.load(f)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    for gym_name in gym_list:
        print(f"Scraping: {gym_name}")
        try:
            query = f"{gym_name} Praha"
            driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}")
            time.sleep(5)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            busyness_block = soup.find("div", {"data-attrid": "kc:/local:busyness"})
            
            occupancy = "N/A"
            if busyness_block:
                match = re.search(r'(\d+)\s*%', busyness_block.get_text())
                if match:
                    occupancy = f"{match.group(1)}%"

            # Uložíme výsledek s časovou značkou
            results[gym_name] = {
                "occupancy": occupancy,
                "last_update": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            }
            print(f"🏆 {gym_name}: {occupancy}")
            
        except Exception as e:
            print(f"❌ Chyba u {gym_name}: {e}")

    driver.quit()

    # Zápis do JSON souboru
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    gyms_to_scrape = ["Form Factory Palladium", "Form Factory Vinohradská"]
    scrape_gyms(gyms_to_scrape)