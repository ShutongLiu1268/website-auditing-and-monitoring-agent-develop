"""Take screenshot with all expandable sections opened."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SCRIPT_DIR = Path(__file__).parent


async def capture_all_content(url, output_filename):
    """Capture screenshot with all expandable sections opened."""
    print(f"\nCapturing ALL content from: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        print("1. Navigating to URL...")
        await page.goto(url, wait_until="commit", timeout=120000)
        print("   [OK] Navigation committed")
        
        print("2. Waiting for page to render (15 seconds)...")
        await asyncio.sleep(15)
        
        print("3. Dismissing cookie banners...")
        try:
            await page.click('button:has-text("Accept")', timeout=5000)
            print("   Clicked: Accept")
        except:
            print("   No cookie banner found")
        
        print("4. Clicking expandable sections...")
        # Try to click common expandable sections
        expandable_selectors = [
            'button:has-text("Tech Specs")',
            'button:has-text("Features")',
            'button:has-text("Specifications")',
            'button:has-text("Details")',
            'button:has-text("Show more")',
            'button:has-text("Expand")',
            'button:has-text("+")',
            '[aria-expanded="false"]',
            '.accordion-button',
            '.tab-button',
        ]
        
        for selector in expandable_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    try:
                        if await element.is_visible(timeout=2000):
                            await element.click()
                            await asyncio.sleep(1)
                            print(f"   Clicked: {selector}")
                    except:
                        pass
            except:
                pass
        
        print("5. Scrolling to load all content...")
        scroll_count = 0
        max_scrolls = 100
        scroll_step = 500
        scroll_position = 0
        
        while scroll_count < max_scrolls:
            await page.evaluate(f"window.scrollTo(0, {scroll_position})")
            await asyncio.sleep(1)
            scroll_position += scroll_step
            scroll_count += 1
            
            current_scroll = await page.evaluate("window.pageYOffset")
            max_scroll = await page.evaluate("document.body.scrollHeight - window.innerHeight")
            
            if current_scroll >= max_scroll - 100:
                print(f"   Reached bottom, doing extra scrolls")
                for i in range(15):
                    await page.evaluate(f"window.scrollTo(0, {scroll_position})")
                    await asyncio.sleep(1)
                    scroll_position += scroll_step
                break
        
        print(f"   Scrolled {scroll_count} times")
        
        print("6. Scrolling back to top...")
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(3)
        
        print("7. Taking full-page screenshot...")
        output_path = SCRIPT_DIR / output_filename
        await page.screenshot(path=str(output_path), full_page=True, timeout=300000)
        print(f"   [OK] Screenshot saved to: {output_path}")
        
        await browser.close()
        print("\nDone!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python screenshot_all.py <URL> <output_filename>")
        sys.exit(1)
    
    url = sys.argv[1]
    filename = sys.argv[2]
    asyncio.run(capture_all_content(url, filename))
