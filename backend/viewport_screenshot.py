"""Simple script to take a viewport screenshot of a single URL."""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

SCRIPT_DIR = Path(__file__).parent


async def capture_screenshot(url, output_filename):
    """Capture a viewport screenshot (visible area only)."""
    print(f"\nCapturing viewport screenshot of: {url}")
    print(f"Output: {output_filename}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        print("1. Navigating to URL...")
        await page.goto(url, wait_until="commit", timeout=120000)
        print("   [OK] Navigation committed")

        print("2. Waiting for page to render (15 seconds)...")
        await asyncio.sleep(15)

        print("3. Handling geo-location prompt...")
        geo_selectors = [
            'button:has-text("Stay on")',
            'a:has-text("Stay on")',
            'button:has-text("Continue to")',
            'a:has-text("Continue to")',
            '[data-testid*="stay"]',
            '[data-testid*="continue"]',
        ]

        for selector in geo_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=3000):
                    await element.click()
                    print(f"   Clicked: {selector}")
                    await asyncio.sleep(3)
                    break
            except:
                continue

        print("   Geo-location handling complete")

        print("4. Dismissing cookie banners...")
        cookie_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("Accept Cookies")',
            'button:has-text("I Agree")',
            'button:has-text("Got it")',
            'button:has-text("Allow")',
            '.cookie-banner button',
            '#onetrust-accept-btn-handler',
            '.accept-btn',
        ]

        for selector in cookie_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=2000):
                    await element.click()
                    print(f"   Clicked: {selector}")
                    await asyncio.sleep(1)
                    break
            except:
                continue

        print("   Cookie banner handling complete")

        print("5. Taking viewport screenshot...")
        output_path = SCRIPT_DIR / output_filename

        # Take viewport screenshot (visible area only)
        await page.screenshot(path=str(output_path), full_page=False, timeout=120000)
        print(f"   [OK] Screenshot saved to: {output_path}")

        await browser.close()
        print("\nDone!")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python viewport_screenshot.py <URL> <output_filename>")
        print("Example: python viewport_screenshot.py https://www.dell.com/en-gb uk_homepage.png")
        sys.exit(1)

    url = sys.argv[1]
    filename = sys.argv[2]
    asyncio.run(capture_screenshot(url, filename))
