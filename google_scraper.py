import os
import time
import re
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def scrape_gyms(gym_list):
    results = {}
    
    # 1. Načtení dat (ošetření starého i nového formátu)
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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=cs-CZ")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    for gym_name in gym_list:
        print(f"🔍 Prověřuji: {gym_name}")
        try:
            query = f"{gym_name} Praha"
            driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}")
            
            time.sleep(5) # Počkáme na načtení stránky

            # --- OŠETŘENÍ COOKIE LISTY ---
            # Google často zobrazí okno "Předtím než začnete..."
            try:
                # Hledáme tlačítko "Přijmout vše" (česká verze má text "Přijmout vše")
                # Zkusíme to přes ID nebo text
                cookie_buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in cookie_buttons:
                    if "Přijmout" in btn.text or "Accept all" in btn.text:
                        btn.click()
                        print("✅ Cookies potvrzeny")
                        time.sleep(3)
                        break
            except:
                pass # Pokud okno není, jedeme dál

            # Čekání na vykreslení grafů
            time.sleep(8)
            
            # Screenshot pro tvou kontrolu v Artifacts
            filename = f"debug_{gym_name.replace(' ', '_')}.png"
            driver.save_screenshot(filename)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            occupancy = "N/A"
            status_text = "Nezjištěno"

            # Hledání v celém textu stránky (nejrobustnější metoda)
            full_text = soup.get_text(separator=' ', strip=True)
            
            # Hledáme vzor "Živě: XX %" nebo "Live: XX %"
            match = re.search(r'(?:Živě|Live):\s*(\d+)\s*%', full_text)
            
            if not match:
                # Alternativní hledání - jen procenta v blízkosti slova Živě
                if "Živě" in full_text:
                    parts = full_text.split("Živě")
                    if len(parts) > 1:
                        m = re.search(r'(\d+)\s*%', parts[1][:50])
                        if m: match = m

            if match:
                occupancy = f"{match.group(1)}%"
                # Pokusíme se najít i textový popis (vše za procenty až k tečce)
                status_match = re.search(match.group(0) + r'\s*([^.]+)', full_text)
                if status_match:
                    status_text = status_match.group(1).strip()

            # 2. BEZPEČNÉ ULOŽENÍ DO HISTORIE (oprava chyby 'dict' object has no attribute 'append')
            new_entry = {
                "occupancy": occupancy,
                "status": status_text,
                "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            }

            if gym_name not in results or not isinstance(results[gym_name], list):
                results[gym_name] = []
            
            results[gym_name].append(new_entry)
            
            # Držíme historii posledních 50 měření
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
    gyms_to_scrape = ["Form Factory Palladium", "Form Factory Vinohradská"]
    scrape_gyms(gyms_to_scrape)