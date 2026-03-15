import os
import time
import re
import json
import random
from datetime import datetime
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

def scrape_gyms(gym_list):
    results = {}
    # Načtení historie
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                results = json.load(f)
        except:
            results = {}

    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    print("🚀 Startuji undetected-chrome...")
    try:
        driver = uc.Chrome(options=options, headless=True)
    except Exception as e:
        print(f"❌ Chyba startu prohlížeče: {e}")
        return

    for gym_name in gym_list:
        try:
            print(f"🔍 Hledám: {gym_name}")
            # Simulace reálného hledání s českým jazykem
            driver.get(f"https://www.google.com/search?q={gym_name.replace(' ', '+')}+Praha&hl=cs")
            
            # Google v cloudu potřebuje čas na vykreslení grafů
            time.sleep(15) 
            
            # Uložení screenshotu pro ladění (uvidíš v Artifacts)
            safe_name = gym_name.replace(' ', '_')
            driver.save_screenshot(f"{safe_name}.png")
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            occupancy = "N/A"
            status_text = "Nezjištěno"

            # 1. Pokus: Hledání v celém textu (hledáme "XX %")
            full_text = soup.get_text(separator=' ', strip=True)
            match = re.search(r'(?:Živě|Live|Právě teď|vytížení):\s*(\d+)\s*%', full_text, re.IGNORECASE)
            
            if not match:
                # 2. Pokus: Hledání v aria-labels (pro čtečky)
                labels = soup.find_all(attrs={"aria-label": True})
                for l in labels:
                    if '%' in l['aria-label'] and any(x in l['aria-label'] for x in ["Živě", "Live", "vytížení"]):
                        m = re.search(r'(\d+)\s*%', l['aria-label'])
                        if m:
                            match = m
                            break

            if match:
                occupancy = f"{match.group(1)}%"
                print(f"✅ Úspěch: {gym_name} -> {occupancy}")
            else:
                print(f"⚠️ Procento pro {gym_name} nenalezeno (zkontroluj screenshot)")

            # Uložení do historie
            new_entry = {
                "occupancy": occupancy,
                "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            }
            
            if gym_name not in results or not isinstance(results[gym_name], list):
                results[gym_name] = []
            
            results[gym_name].append(new_entry)
            # Limit 100 záznamů
            if len(results[gym_name]) > 100:
                results[gym_name] = results[gym_name][-100:]

        except Exception as e:
            print(f"❌ Kritická chyba u {gym_name}: {e}")
        
        time.sleep(random.uniform(5, 10))

    driver.quit()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("🏁 Hotovo, data.json aktualizován.")

if __name__ == "__main__":
    scrape_gyms(["Form Factory Palladium", "Form Factory Vinohradská"])