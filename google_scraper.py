import asyncio
from datetime import datetime
import json
import os
import re

# Importy pro nejnovější Crawlee
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from crawlee.models import Request # Přidáno pro opravu chyby

async def main():
    gyms = ["Form Factory Palladium", "Form Factory Vinohradská"]
    
    # Nastavení crawleru
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=10,
        headless=True,
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext):
        # V nové verzi se k user_data přistupuje přes context.request.user_data
        gym_name = context.request.user_data.get('gym_name')
        page = context.page
        
        try:
            # Navigace na Google
            await page.goto(context.request.url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(8) 
            
            content = await page.content()
            # Regex pro vytížení
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

    # --- TADY JE OPRAVA ---
    # Místo seznamu slovníků [{}, {}] vytváříme seznam objektů Request
    requests = [
        Request(
            url=f"https://www.google.com/search?q={g.replace(' ', '+')}+Praha&hl=cs",
            user_data={'gym_name': g}
        ) for g in gyms
    ]
    
    # Spuštění
    await crawler.run(requests)

    # --- Export do data.json (beze změny) ---
    final_results = {}
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                final_results = json.load(f)
        except:
            final_results = {}

    storage_path = './storage/datasets/default/'
    if os.path.exists(storage_path):
        for file in sorted(os.listdir(storage_path)):
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
                    final_results[name] = final_results[name][-100:]

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    print("🏁 Hotovo.")

if __name__ == '__main__':
    asyncio.run(main())