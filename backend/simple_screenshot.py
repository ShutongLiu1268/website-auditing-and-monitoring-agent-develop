"""Simple script to take a screenshot of a single URL."""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

SCRIPT_DIR = Path(__file__).parent


async def capture_screenshot(url, output_filename):
    """Capture a single page screenshot."""
    print(f"\nCapturing screenshot of: {url}")
    print(f"Output: {output_filename}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        print("1. Navigating to URL...")
        await page.goto(url, wait_until="commit", timeout=120000)
        print("   [OK] Navigation committed")
        
        print("2. Waiting for page to render (10 seconds)...")
        await asyncio.sleep(10)
        
        print("3. Dismissing cookie banners...")
        try:
            await page.click('button:has-text("Accept")', timeout=5000)
            print("   Clicked: Accept")
        except:
            print("   No cookie banner found or already dismissed")
        
        print("4. Scrolling to load all content...")
        # Scroll more slowly with longer waits to ensure all content loads
        scroll_count = 0
        max_scrolls = 100  # Increased to 100
        scroll_step = 500  # Smaller steps for more thorough scrolling
        scroll_position = 0
        
        while scroll_count < max_scrolls:
            await page.evaluate(f"window.scrollTo(0, {scroll_position})")
            await asyncio.sleep(1)  # Longer wait (1 second instead of 0.5)
            scroll_position += scroll_step
            scroll_count += 1
            
            # Get current scroll position
            current_scroll = await page.evaluate("window.pageYOffset")
            max_scroll = await page.evaluate("document.body.scrollHeight - window.innerHeight")
            
            # If we've reached the bottom, continue scrolling a bit more to be sure
            if current_scroll >= max_scroll - 100:
                print(f"   Reached bottom, doing extra scrolls to ensure all content loaded")
                # Do 10 more scrolls to be absolutely sure
                for i in range(10):
                    await page.evaluate(f"window.scrollTo(0, {scroll_position})")
                    await asyncio.sleep(1)
                    scroll_position += scroll_step
                break
        
        print(f"   Scrolled {scroll_count} times")
        
        print("5. Scrolling back to top...")
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(2)
        
        print("6. Getting actual content height...")
        content_height = await page.evaluate("""
            () => {
                const body = document.body;
                const html = document.documentElement;
                const content = document.querySelector('main, .main-content, [role="main"]');
                
                if (content) {
                    const rect = content.getBoundingClientRect();
                    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    return Math.max(rect.height, rect.bottom - rect.top);
                }
                
                return Math.max(
                    body.scrollHeight,
                    body.offsetHeight,
                    html.clientHeight,
                    html.scrollHeight,
                    html.offsetHeight
                );
            }
        """)
        print(f"   Content height: {content_height}px")
        
        print("7. Taking full-page screenshot...")
        output_path = SCRIPT_DIR / output_filename
        
        # Take full-page screenshot
        await page.screenshot(path=str(output_path), full_page=True, timeout=120000)
        print(f"   [OK] Screenshot saved to: {output_path}")
        
        await browser.close()
        print("\nDone!")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python simple_screenshot.py <URL> <output_filename>")
        print("Example: python simple_screenshot.py https://www.dell.com/en-gb uk_homepage.png")
        sys.exit(1)
    
    url = sys.argv[1]
    filename = sys.argv[2]
    asyncio.run(capture_screenshot(url, filename))
