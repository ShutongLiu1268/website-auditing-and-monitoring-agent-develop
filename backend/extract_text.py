"""Extract full page text for R2 audit."""

import asyncio
from playwright.async_api import async_playwright

URL = "https://www.dell.com/en-us/shop/laptop-computers/spd/xps13dx13260#configure-anchor"


async def main():
    print("Extracting full page text for R2 audit...")
    print("="*60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            permissions=["geolocation"],
            ignore_https_errors=True,
        )
        page = await context.new_page()

        print("Navigating to URL...")
        await page.goto(URL, wait_until="commit", timeout=120000)
        await asyncio.sleep(10)

        print("Dismissing cookie banners...")
        try:
            element = page.locator('button:has-text("Accept")').first
            if await element.is_visible(timeout=2000):
                await element.click()
        except:
            pass

        print("Scrolling to load all content...")
        page_height = await page.evaluate("document.body.scrollHeight")
        scroll_position = 0
        for _ in range(30):
            await page.evaluate(f"window.scrollTo(0, {scroll_position})")
            await asyncio.sleep(0.5)
            scroll_position += 1080
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(2)

        print("Extracting full text...")
        full_text = await page.locator('body').inner_text()

        # Save to file
        with open("pdp_text.txt", "w", encoding="utf-8") as f:
            f.write(full_text)

        print(f"Extracted {len(full_text)} characters")
        print("Saved to: pdp_text.txt")

        await browser.close()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
