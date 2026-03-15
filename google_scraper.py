import asyncio
from datetime import datetime
import json
import os
import re

# Tento import je pro verzi 0.4.0 a novější (včetně v1.0)
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
            # Přidáme hl=cs pro vynucení češtiny přímo v URL
            await page.goto(context.request.url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(8) 
            
            content = await page.content()
            # Robustnější regex pro češtinu i angličtinu
            match = re.search(r'(?:Živě|Live|Právě teď|vytížení|Busy|Popular times):\s*(\d+)\s*%', content, re.IGNORECASE)
            
            occupancy = "N/A"
            if match:
                occupancy = f"{match.group(1)}%"
                print(f"✅ {gym_name}: {occupancy}")
            
            await context.push_data({
                'gym': gym_name,
                'occupancy': occupancy,
                'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            })
        except Exception as e:
            print(f"❌ Chyba u {gym_name}: {e}")

    # Spuštění
    requests = [{'url': f"https://www.google.com/search?q={g.replace(' ', '+')}+Praha&hl=cs", 'user_data': {'gym_name': g}} for g in gyms]
    await crawler.run(requests)

    # --- Export do data.json ---
    final_results = {}
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                final_results = json.load(f)
        except:
            final_results = {}

    storage_path = './storage/datasets/default/'
    if os.path.exists(storage_path):
        for file in os.listdir(storage_path):
            if file.endswith('.json'):
                with open(os.path.join(storage_path, file), 'r', encoding='utf-8') as f:
                    item = json.load(f)
                    name = item['gym']
                    if name not in final_results: final_results[name] = []
                    final_results[name].append({"occupancy": item['occupancy'], "timestamp": item['timestamp']})
                    final_results[name] = final_results[name][-100:]

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    print("🏁 Hotovo.")

if __name__ == '__main__':
    asyncio.run(main())