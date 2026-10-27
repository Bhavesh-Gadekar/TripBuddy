import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # 1. Home Laptop
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        await page.goto("http://127.0.0.1:3000", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="docs/screenshots/home_laptop.png")
        print("Captured home_laptop.png")

        # 2. Home Tablet
        page_tablet = await browser.new_page(viewport={"width": 768, "height": 1024})
        await page_tablet.goto("http://127.0.0.1:3000", wait_until="domcontentloaded")
        await page_tablet.wait_for_timeout(2000)
        await page_tablet.screenshot(path="docs/screenshots/home_tablet.png")
        print("Captured home_tablet.png")

        # 3. Search Results Laptop
        page_search = await browser.new_page(viewport={"width": 1280, "height": 800})
        await page_search.goto("http://127.0.0.1:3000/search?city=Goa", wait_until="domcontentloaded")
        await page_search.wait_for_timeout(2000)
        await page_search.screenshot(path="docs/screenshots/search_laptop.png")
        print("Captured search_laptop.png")

        # 4. Search Results Tablet
        page_search_tab = await browser.new_page(viewport={"width": 768, "height": 1024})
        await page_search_tab.goto("http://127.0.0.1:3000/search?city=Goa", wait_until="domcontentloaded")
        await page_search_tab.wait_for_timeout(2000)
        await page_search_tab.screenshot(path="docs/screenshots/search_tablet.png")
        print("Captured search_tablet.png")

        # 5. Listing Detail Laptop
        page_detail = await browser.new_page(viewport={"width": 1280, "height": 800})
        await page_detail.goto("http://127.0.0.1:3000/rooms/lst-goa-001", wait_until="domcontentloaded")
        await page_detail.wait_for_timeout(2000)
        await page_detail.screenshot(path="docs/screenshots/listing_laptop.png")
        print("Captured listing_laptop.png")

        # 6. Listing Detail Tablet
        page_detail_tab = await browser.new_page(viewport={"width": 768, "height": 1024})
        await page_detail_tab.goto("http://127.0.0.1:3000/rooms/lst-goa-001", wait_until="domcontentloaded")
        await page_detail_tab.wait_for_timeout(2000)
        await page_detail_tab.screenshot(path="docs/screenshots/listing_tablet.png")
        print("Captured listing_tablet.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture())

