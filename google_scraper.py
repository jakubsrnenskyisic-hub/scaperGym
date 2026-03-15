import asyncio
from datetime import datetime
import json
import os
import re

# Pokus o import Crawlee s více možnostmi (pro různé verze)
try:
    from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
except ImportError:
    from crawlee import PlaywrightCrawler, PlaywrightCrawlingContext

async def main():
    gyms = ["Form Factory Palladium", "Form Factory Vinohradská"]
    
    # Nastavení crawleru
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=10,
        browser_type='chromium',
        headless=True,
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext):
        gym_name = context.request.user_data.get('gym_name')
        page = context.page
        
        try:
            # Navigace na Google vyhledávání
            await page.goto(context.request.url, wait_until='networkidle')
            await asyncio.sleep(7) # Čas na načtení dynamických grafů
            
            content = await page.content()
            # Hledání procent (regex)
            match = re.search(r'(?:Živě|Live|Právě teď|vytížení):\s*(\d+)\s*%', content, re.IGNORECASE)
            
            occupancy = "N/A"
            if match:
                occupancy = f"{match.group(1)}%"
                print(f"✅ {gym_name}: {occupancy}")
            else:
                print(f"⚠️ {gym_name}: Procento nenalezeno.")
            
            # Uložení do dočasného úložiště Crawlee
            await context.push_data({
                'gym': gym_name,
                'occupancy': occupancy,
                'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            })
        except Exception as e:
            print(f"❌ Chyba u {gym_name}: {e}")

    # Příprava požadavků
    requests = [
        {
            'url': f"https://www.google.com/search?q={g.replace(' ', '+')}+Praha&hl=cs", 
            'user_data': {'gym_name': g}
        } for g in gyms
    ]
    
    # Spuštění crawleru
    await crawler.run(requests)

    # --- PŘELITÍ DAT DO data.json ---
    final_results = {}
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                final_results = json.load(f)
        except:
            final_results = {}

    # Projdeme složku, kam Crawlee ukládá výsledky
    storage_path = './storage/datasets/default/'
    if os.path.exists(storage_path):
        for file in os.listdir(storage_path):
            if file.endswith('.json'):
                with open(os.path.join(storage_path, file), 'r', encoding='utf-8') as f:
                    item = json.load(f)
                    name = item['gym']
                    if name not in final_results:
                        final_results[name] = []
                    
                    final_results[name].append({
                        "occupancy": item['occupancy'],
                        "timestamp": item['timestamp']
                    })
                    # Udržíme jen posledních 100 záznamů pro každé fitko
                    final_results[name] = final_results[name][-100:]

    # Uložení finálního souboru
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    print("🏁 Data úspěšně uložena do data.json")

if __name__ == '__main__':
    asyncio.run(main())