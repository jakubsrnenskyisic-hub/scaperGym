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
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                results = json.load(f)
        except:
            results = {}

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080") # Větší okno, aby se graf vešel
    options.add_argument("--lang=cs-CZ")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    for gym_name in gym_list:
        print(f"🔍 Prověřuji: {gym_name}")
        try:
            query = f"{gym_name} Praha"
            driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}")
            
            # Počkáme déle, Google v cloudu může být pomalý
            time.sleep(12)
            
            # --- DEBUG: Uložíme fotku toho, co robot vidí ---
            driver.save_screenshot(f"debug_{gym_name.replace(' ', '_')}.png")
            print(f"📸 Screenshot uložen pro {gym_name}")
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            occupancy = "N/A"
            status_text = "Nezjištěno"

            # Hledání v celém textu stránky (nejstabilnější)
            full_page_text = soup.get_text(separator=' ', strip=True)
            
            # Hledáme vzor "Živě: XX%" nebo jen "XX %" v okolí slova "vytížení"
            match = re.search(r'(?:Živě|Live):\s*(\d+)\s*%', full_page_text)
            if not match:
                # Zkusíme najít jakékoliv procento, které následuje po "Živě"
                live_pos = full_page_text.find("Živě")
                if live_pos != -1:
                    snippet = full_page_text[live_pos:live_pos+50]
                    match = re.search(r'(\d+)\s*%', snippet)

            if match:
                occupancy = f"{match.group(1)}%"
                # Zkusíme vytáhnout i ten text (např. Nižší vytížení)
                status_match = re.search(r'(?:Živě):\s*\d+\s*%\s*([^.]+)', full_page_text)
                if status_match:
                    status_text = status_match.group(1).strip()

            new_entry = {
                "occupancy": occupancy,
                "status": status_text,
                "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            }

            if gym_name not in results:
                results[gym_name] = []
            results[gym_name].append(new_entry)
            if len(results[gym_name]) > 50:
                results[gym_name] = results[gym_name][-50:]

            print(f"🏆 {gym_name}: {occupancy} | {status_text}")
            
        except Exception as e:
            print(f"❌ Chyba: {e}")

    driver.quit()
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    gyms_to_scrape = ["Form Factory Palladium", "Form Factory Vinohradská"]
    scrape_gyms(gyms_to_scrape)