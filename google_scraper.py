import asyncio
from datetime import datetime
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
import json
import os

async def main():
    # Seznam fitek, které chceme sledovat
    gyms = ["Form Factory Palladium", "Form Factory Vinohradská"]
    
    # Inicializace Crawlee Crawleru
    # headless=True je pro GitHub nezbytné
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=10,
        browser_type='chromium',
        headless=True,
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext):
        gym_name = context.request.user_data.get('gym_name')
        context.log.info(f"🔍 Zpracovávám: {gym_name}")

        page = context.page
        # Počkáme, až se objeví hlavní výsledky nebo grafy
        # Používáme selektory z Crawlee blogu, které jsou stabilnější
        try:
            # Čekáme na vykreslení stránky (max 20s)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(5) # Krátká pauza na JS grafy

            # Zkusíme vytáhnout text celé stránky
            content = await page.content()
            
            # Hledání procent pomocí regulárního výrazu přímo v HTML/Textu
            import re
            match = re.search(r'(?:Živě|Live|Právě teď|vytížení):\s*(\d+)\s*%', content, re.IGNORECASE)
            
            occupancy = "N/A"
            if match:
                occupancy = f"{match.group(1)}%"
                context.log.info(f"✅ Nalezeno pro {gym_name}: {occupancy}")
            else:
                context.log.warning(f"⚠️ Procento pro {gym_name} nenalezeno.")
                # Uděláme screenshot pro debug, pokud to nenajde data
                await page.screenshot(path=f"error_{gym_name.replace(' ', '_')}.png")

            # Uložíme výsledek do Crawlee datasetu (automaticky vytváří JSON)
            await context.push_data({
                'gym': gym_name,
                'occupancy': occupancy,
                'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            })

        except Exception as e:
            context.log.error(f"❌ Chyba při zpracování {gym_name}: {e}")

    # Vytvoření seznamu URL pro vyhledávání
    requests = []
    for gym in gyms:
        url = f"https://www.google.com/search?q={gym.replace(' ', '+')}+Praha&hl=cs"
        requests.append({'url': url, 'user_data': {'gym_name': gym}})

    # Spuštění
    await crawler.run(requests)

    # Po skončení převedeme data z Crawlee storage do tvého data.json
    # Crawlee ukládá data do složky ./storage/datasets/default/
    final_data = {}
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            final_data = json.load(f)

    # Načtení nových dat z Crawlee exportu
    # (Zjednodušeno pro tvůj stávající formát)
    storage_path = './storage/datasets/default/'
    if os.path.exists(storage_path):
        for filename in os.listdir(storage_path):
            if filename.endswith('.json'):
                with open(os.path.join(storage_path, filename), 'r', encoding='utf-8') as f:
                    item = json.load(f)
                    name = item['gym']
                    if name not in final_data: final_data[name] = []
                    final_data[name].append({
                        "occupancy": item['occupancy'],
                        "timestamp": item['timestamp']
                    })
                    # Limit 100 záznamů
                    final_data[name] = final_data[name][-100:]

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    asyncio.run(main())