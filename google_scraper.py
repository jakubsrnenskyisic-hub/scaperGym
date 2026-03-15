import asyncio
from datetime import datetime
import json
import os
import re

# Nejstabilnější importy pro verzi 1.0+
from crawlee import Request
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

async def main():
    gyms = ["Form Factory Palladium", "Form Factory Vinohradská"]
    
    # Nastavení crawleru
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=10,
        headless=True,
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext):
        # Přístup k datům v nové verzi
        gym_name = context.request.user_data.get('gym_name')
        page = context.page
        
        try:
            # Navigace s češtinou
            await page.goto(context.request.url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(8) # Čas na grafy
            
            content = await page.content()
            # Regex pro vytížení (CZ/EN)
            match = re.search(r'(?:Živě|Live|Právě teď|vytížení|Busy|Popular times):\s*(\d+)\s*%', content, re.IGNORECASE)
            
            occupancy = "N/A"
            if match:
                occupancy = f"{match.group(1)}%"
                print(f"✅ {gym_name}: {occupancy}")
            else:
                print(f"⚠️ {gym_name}: Procento nenalezeno.")
            
            # Uložení do Crawlee datasetu
            await context.push_data({
                'gym': gym_name,
                'occupancy': occupancy,
                'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            })
        except Exception as e:
            print(f"❌ Chyba u {gym_name}: {e}")

    # Vytvoření požadavků pomocí správné třídy Request
    requests = [
        Request(
            url=f"https://www.google.com/search?q={g.replace(' ', '+')}+Praha&hl=cs",
            user_data={'gym_name': g}
        ) for g in gyms
    ]
    
    # Spuštění
    await crawler.run(requests)

    # --- PŘELITÍ DAT DO data.json ---
    final_results = {}
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                final_results = json.load(f)
        except:
            final_results = {}

    # Crawlee ukládá do storage/datasets/default/
    storage_path = './storage/datasets/default/'
    if os.path.exists(storage_path):
        files = sorted([f for f in os.listdir(storage_path) if f.endswith('.json')])
        for file in files:
            with open(os.path.join(storage_path, file), 'r', encoding='utf-8') as f:
                item = json.load(f)
                name = item.get('gym')
                if name:
                    if name not in final_results:
                        final_results[name] = []
                    final_results[name].append({
                        "occupancy": item['occupancy'],
                        "timestamp": item['timestamp']
                    })
                    final_results[name] = final_results[name][-100:]

    # Uložení finálního JSONu
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    print("🏁 Všechna data uložena do data.json")

if __name__ == '__main__':import asyncio
from datetime import datetime
import json
import os
import re

# Importy pro verzi 1.0+
from crawlee import Request
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

async def main():
    gyms = ["Form Factory Palladium", "Form Factory Vinohradská"]
    
    # Nastavení crawleru
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=10,
        headless=True,
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext):
        gym_name = context.request.user_data.get('gym_name')
        page = context.page
        
        try:
            await page.goto(context.request.url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(8) 
            
            content = await page.content()
            # Regex pro vytížení (CZ/EN)
            match = re.search(r'(?:Živě|Live|Právě teď|vytížení|Busy|Popular times):\s*(\d+)\s*%', content, re.IGNORECASE)
            
            occupancy = "N/A"
            if match:
                occupancy = f"{match.group(1)}%"
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

    # --- TADY BYLA CHYBA (PŘIDÁNO unique_key) ---
    requests = []
    for g in gyms:
        requests.append(
            Request(
                url=f"https://www.google.com/search?q={g.replace(' ', '+')}+Praha&hl=cs",
                user_data={'gym_name': g},
                unique_key=f"{g.replace(' ', '_').lower()}_{datetime.now().strftime('%H')}" # Unikátní klíč pro každou hodinu
            )
        )
    
    await crawler.run(requests)

    # --- PŘELITÍ DAT DO data.json ---
    final_results = {}
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                final_results = json.load(f)
        except:
            final_results = {}

    storage_path = './storage/datasets/default/'
    if os.path.exists(storage_path):
        files = sorted([f for f in os.listdir(storage_path) if f.endswith('.json')])
        for file in files:
            with open(os.path.join(storage_path, file), 'r', encoding='utf-8') as f:
                item = json.load(f)
                name = item.get('gym')
                if name:
                    if name not in final_results:
                        final_results[name] = []
                    final_results[name].append({
                        "occupancy": item['occupancy'],
                        "timestamp": item['timestamp']
                    })
                    final_results[name] = final_results[name][-100:]

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    print("🏁 Všechna data uložena do data.json")

if __name__ == '__main__':
    asyncio.run(main())
    asyncio.run(main())