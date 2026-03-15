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
    options.add_argument("--lang=cs-CZ")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    for gym_name in gym_list:
        print(f"🔍 Prověřuji: {gym_name}")
        try:
            query = f"{gym_name} Praha"
            driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}")
            time.sleep(10) # Čas na vykreslení JS grafů
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            occupancy = "N/A"
            status_text = "Nezjištěno"

            # 1. NAJDEME TEXT "Živě" (v jakémkoliv divu/spanu)
            live_element = soup.find(string=re.compile(r"Živě:|Live:"))
            
            if live_element:
                # Najdeme nejbližší nadřazený kontejner, který obsahuje ten text
                parent_container = live_element.find_parent()
                
                # STATUS: Vytáhneme text, co je hned za "Živě:" (např. "Nižší vytížení")
                status_text = parent_container.get_text(strip=True).replace("Živě:", "").strip()
                
                # PROCENTA: Teď zkusíme najít procenta v celém bloku "Oblíbené časy"
                # Prohledáme všechny sousední a nadřazené divy a hledáme aria-label s %
                popular_times_block = live_element.find_parent("div", {"class": True}) # Hledáme nejbližší velký blok
                
                # Pokud nenajdeme přímo, prohledáme celé okolí
                search_area = live_element.find_parent(id=re.compile(r"itRa")) or live_element.find_parent("div")
                
                # Hledáme jakékoliv procento v okolí "Živě"
                all_texts = search_area.get_text(separator=' ')
                match = re.search(r'(\d+)\s*%', all_texts)
                
                if match:
                    occupancy = f"{match.group(1)}%"
                else:
                    # Poslední záchrana: Prohledat aria-labels v celém okolí grafu
                    labels = search_area.find_all(attrs={"aria-label": True})
                    for l in labels:
                        if '%' in l['aria-label']:
                            m = re.search(r'(\d+)\s*%', l['aria-label'])
                            if m:
                                occupancy = f"{m.group(1)}%"
                                break

            # 2. Uložení do historie
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
            print(f"❌ Chyba u {gym_name}: {e}")

    driver.quit()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("✅ data.json aktualizován.")

if __name__ == "__main__":
    # Tady si doplňuj fitka podle potřeby
    gyms_to_scrape = ["JOHN REED Fitness Praha"]
    scrape_gyms(gyms_to_scrape)