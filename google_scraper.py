import asyncio
from datetime import datetime
import json
import os
import re

from crawlee import Request
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

async def main():
    gyms = ["Form Factory Palladium", "Form Factory Vinohradská"]
    
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=10,
        headless=True,
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext):
        gym_name = context.request.user_data.get('gym_name')
        page = context.page
        
        try:
            # Přidáme hl=cs do URL pro vynucení češtiny, ale skript zvládne i EN
            await page.goto(context.request.url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(10) # Necháme grafy pořádně načíst
            
            content = await page.content()
            
            # Mnohem širší regex pro nalezení procent (CZ i EN Google)
            # Hledá: "Živě: 45%", "Live: 45%", "Busy: 45%", "Právě teď: 45%" atd.
            patterns = [
                r'(?:Živě|Live|Právě teď|vytížení|Busy|Popular times|Currently):\s*(\d+)\s*%',
                r'(\d+)\s*%\s*(?:vytížení|busy|full)'
            ]
            
            occupancy = "N/A"
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    occupancy = f"{match.group(1)}%"
                    break
            
            if occupancy != "N/A":
                print(f"✅ {gym_name}: {occupancy}")
            else:
                print(f"⚠️ {gym_name}: Procento nenalezeno.")
            
            await context.push_data({
                'gym': gym_name,
                'occupancy': occupancy,
                'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            })
        except Exception as e:
            print(f"❌ Chyba u {gym_name}: {e}")

    # Vytvoření požadavků
    requests = [
        Request(
            url=f"https://www.google.com/search?q={g.replace(' ', '+')}+Praha&hl=cs",
            user_data={'gym_name': g},
            unique_key=f"{g.replace(' ', '_').lower()}_{datetime.now().strftime('%H_%M')}"
        ) for g in gyms
    ]
    
    await crawler.run(requests)

    # --- OPRAVENÉ PŘELITÍ DAT DO data.json ---
    final_results = {}
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    final_results = loaded
        except:
            final_results = {}

    storage_path = './storage/datasets/default/'
    if os.path.exists(storage_path):
        for file in os.listdir(storage_path):
            if file.endswith('.json') and file != '__metadata__.json':
                with open(os.path.join(storage_path, file), 'r', encoding='utf-8') as f:
                    item = json.load(f)
                    name = item.get('gym')
                    if name:
                        # Zajištění, že pod klíčem 'name' je SEZNAM (list)
                        if name not in final_results or not isinstance(final_results[name], list):
                            final_results[name] = []
                        
                        final_results[name].append({
                            "occupancy": item['occupancy'],
                            "timestamp": item['timestamp']
                        })
                        final_results[name] = final_results[name][-100:]

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    print(f"🏁 Hotovo. Uloženo do data.json.")

if __name__ == '__main__':
    asyncio.run(main())