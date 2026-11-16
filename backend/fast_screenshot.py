"""Fast screenshot script - minimal operations for quick capture."""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

SCRIPT_DIR = Path(__file__).parent


async def capture_screenshot(url, output_filename):
    """Capture a single page screenshot quickly."""
    print(f"\nCapturing screenshot of: {url}")
    print(f"Output: {output_filename}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        print("1. Navigating to URL...")
        await page.goto(url, wait_until="commit", timeout=120000)
        print("   [OK] Navigation committed")

        print("2. Waiting for page to render (5 seconds)...")
        await asyncio.sleep(5)

        print("3. Handling geo-location prompt...")
        geo_selectors = [
            'button:has-text("Stay on")',
            'a:has-text("Stay on")',
            'button:has-text("Continue to")',
            'a:has-text("Continue to")',
        ]

        for selector in geo_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=2000):
                    await element.click()
                    print(f"   Clicked: {selector}")
                    await asyncio.sleep(1)
                    break
            except:
                continue

        print("   Geo-location handling complete")

        print("4. Dismissing cookie banners...")
        cookie_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("Accept Cookies")',
            '#onetrust-accept-btn-handler',
        ]

        for selector in cookie_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=1500):
                    await element.click()
                    print(f"   Clicked: {selector}")
                    await asyncio.sleep(0.5)
                    break
            except:
                continue

        print("   Cookie banner handling complete")

        print("5. Hiding navigation elements...")
        await page.evaluate("""
            () => {
                const selectors = [
                    'nav', '.navigation', '.nav-menu', '.header-nav',
                    '.mega-menu', '[role="navigation"]', '.site-header',
                    'header', '.top-nav', '.main-nav', '.primary-nav',
                    '.dell-header', '.global-nav', '.basket-nav', '.cart-nav',
                ];
                selectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                    });
                });
                return true;
            }
        """)
        print("   Navigation elements hidden")

        print("6. Scrolling to load content (10 scrolls)...")
        scroll_count = 0
        max_scrolls = 10
        scroll_step = 800
        scroll_position = 0

        while scroll_count < max_scrolls:
            await page.evaluate(f"window.scrollTo(0, {scroll_position})")
            await asyncio.sleep(0.5)
            scroll_position += scroll_step
            scroll_count += 1

            current_scroll = await page.evaluate("window.pageYOffset")
            max_scroll = await page.evaluate("document.body.scrollHeight - window.innerHeight")

            if current_scroll >= max_scroll - 100:
                print("   Reached bottom")
                break

        print(f"   Scrolled {scroll_count} times")

        print("7. Scrolling back to top...")
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)

        print("8. Taking full-page screenshot...")
        output_path = SCRIPT_DIR / output_filename
        await page.screenshot(path=str(output_path), full_page=True, timeout=120000)
        print(f"   [OK] Screenshot saved to: {output_path}")

        await browser.close()
        print("\nDone!")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fast_screenshot.py <URL> <output_filename>")
        print("Example: python fast_screenshot.py https://www.dell.com/en-us/shop/laptop-computers/spd/dell14sds14270 dell14s_usa.png")
        sys.exit(1)

    url = sys.argv[1]
    filename = sys.argv[2]
    asyncio.run(capture_screenshot(url, filename))
