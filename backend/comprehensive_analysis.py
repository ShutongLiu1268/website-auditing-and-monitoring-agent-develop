"""Comprehensive Analysis: Screenshot + Text Extraction"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SCRIPT_DIR = Path(__file__).parent


async def comprehensive_analysis(url):
    """Extract both screenshot and full text for comprehensive analysis."""
    print(f"\n{'='*60}")
    print("COMPREHENSIVE ANALYSIS")
    print(f"{'='*60}")
    print(f"URL: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # Navigate
        print("\n1. Navigating to URL...")
        await page.goto(url, wait_until="commit", timeout=120000)
        print("   [OK] Navigation committed")
        
        print("2. Waiting for page to render (10 seconds)...")
        await asyncio.sleep(10)
        
        print("3. Dismissing cookie banners...")
        try:
            await page.click('button:has-text("Accept")', timeout=5000)
            print("   Clicked: Accept")
        except:
            print("   No cookie banner found")
        
        # Scroll to load all content
        print("4. Scrolling to load all content...")
        scroll_count = 0
        max_scrolls = 20
        scroll_step = 1080
        scroll_position = 0
        
        while scroll_count < max_scrolls:
            await page.evaluate(f"window.scrollTo(0, {scroll_position})")
            await asyncio.sleep(0.5)
            scroll_position += scroll_step
            scroll_count += 1
        
        print(f"   Scrolled {scroll_count} times")
        
        # Scroll back to top
        print("5. Scrolling back to top...")
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(2)
        
        # Take screenshot
        print("6. Taking full-page screenshot...")
        screenshot_path = SCRIPT_DIR / "comprehensive_screenshot.png"
        await page.screenshot(path=str(screenshot_path), full_page=True, timeout=120000)
        print(f"   [OK] Screenshot saved to: {screenshot_path}")
        
        # Extract text
        print("7. Extracting full text content...")
        text = await page.evaluate("""
            () => {
                return document.body.innerText;
            }
        """)
        
        print(f"   Extracted {len(text)} characters")
        
        # Save text
        text_file = SCRIPT_DIR / "comprehensive_text.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"   [OK] Text saved to: {text_file}")
        
        await browser.close()
        
        print(f"\n{'='*60}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"\nFiles generated:")
        print(f"- Screenshot: {screenshot_path}")
        print(f"- Full Text: {text_file}")
        
        return text


if __name__ == "__main__":
    asyncio.run(comprehensive_analysis("https://www.dell.com/en-gb"))
