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
    
    # 1. Načtení stávajících dat z JSONu (historie)
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                results = json.load(f)
        except Exception as e:
            print(f"⚠️ Nepodařilo se načíst data.json, začínáme znovu: {e}")
            results = {}

    # 2. Nastavení prohlížeče
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=cs-CZ")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    for gym_name in gym_list:
        print(f"🔍 Hledám: {gym_name}")
        try:
            query = f"{gym_name} Praha"
            driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}")
            
            # Počkáme na vykreslení grafů (u GitHubu raději víc)
            time.sleep(10)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            occupancy = "N/A"
            status_text = "Nezjištěno"

            # STRATEGIE A: Hledání textového statusu (např. "Nižší vytížení")
            # Podle tvého HTML je to u elementu se třídou 'yAbdSd'
            live_label = soup.find("span", class_="yAbdSd")
            if live_label and live_label.next_sibling:
                status_text = live_label.next_sibling.strip()

            # STRATEGIE B: Hledání procent v grafu (vnořené divy)
            # Hledáme bar s třídou 'ycghLd' (růžový/aktuální sloupec)
            live_bar = soup.find("div", class_="ycghLd")
            if live_bar:
                # Procenta jsou v aria-label nadřazeného divu
                parent = live_bar.find_parent("div", {"aria-label": True})
                if parent:
                    label = parent['aria-label']
                    match = re.search(r'(\d+)\s*%', label)
                    if match:
                        occupancy = f"{match.group(1)}%"

            # POJISTKA: Pokud stále nemáme procenta, zkusíme najít jakýkoliv 'aria-label', co obsahuje "Živě"
            if occupancy == "N/A":
                all_labels = soup.find_all("div", {"aria-label": re.compile(r'Živě|Live|Vytíženost')})
                for l in all_labels:
                    m = re.search(r'(\d+)\s*%', l['aria-label'])
                    if m:
                        occupancy = f"{m.group(1)}%"
                        break

            # 3. Uložení do historie
            new_entry = {
                "occupancy": occupancy,
                "status": status_text,
                "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            }

            if gym_name not in results:
                results[gym_name] = []
            
            results[gym_name].append(new_entry)

            # Limit historie na posledních 50 záznamů, aby JSON nebyl moc velký
            if len(results[gym_name]) > 50:
                results[gym_name] = results[gym_name][-50:]

            print(f"🏆 {gym_name}: {occupancy} ({status_text})")
            
        except Exception as e:
            print(f"❌ Chyba u {gym_name}: {e}")

    driver.quit()

    # 4. Zápis zpět do JSON souboru
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("✅ Hotovo. Data uložena do data.json")

if __name__ == "__main__":
    # Tady si doplň seznam všech svých fitek
    gyms_to_scrape = [
        "JOHN REED Fitness Praha"
    ]
    scrape_gyms(gyms_to_scrape)