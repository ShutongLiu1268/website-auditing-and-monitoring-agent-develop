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
        
        print("2. Waiting for page to render (15 seconds)...")
        await asyncio.sleep(15)
        
        print("3. Dismissing cookie banners...")
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
        
        print("4. Expanding all accordion/toggle sections...")
        # Try to expand common accordion/toggle elements
        accordion_selectors = [
            'button[aria-expanded="false"]',
            '.accordion-button:not(.collapsed)',
            'details[open="false"] summary',
            '.toggle-button',
            '[data-toggle="collapse"]',
            '.expandable-header',
            '.show-more',
            '.view-more',
            'button:has-text("Show more")',
            'button:has-text("View more")',
            'button:has-text("Expand")',
            'button:has-text("+")',
        ]
        
        for selector in accordion_selectors:
            try:
                elements = page.locator(selector).all()
                for element in elements:
                    try:
                        if await element.is_visible(timeout=1000):
                            await element.click()
                            await asyncio.sleep(0.5)
                    except:
                        continue
            except:
                continue
        
        print("   Accordion expansion complete")
        
        print("5. Clicking through image gallery...")
        # Try to click through image gallery arrows/dots
        gallery_selectors = [
            '.gallery-arrow',
            '.carousel-arrow',
            '.image-arrow',
            '.next-image',
            '.prev-image',
            '.gallery-dot',
            '.carousel-dot',
            '.image-dot',
            '[data-gallery-next]',
            '[data-gallery-prev]',
        ]
        
        # Click next arrow multiple times to cycle through images
        for _ in range(5):
            for selector in gallery_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=1000):
                        await element.click()
                        await asyncio.sleep(1)
                        break
                except:
                    continue
        
        print("   Image gallery cycling complete")
        
        print("6. Clicking through all tabs...")
        # Try to click through tab navigation
        tab_selectors = [
            '.tab-button',
            '.tab-link',
            '[role="tab"]',
            '.nav-tab',
            '.tab-item',
        ]
        
        for selector in tab_selectors:
            try:
                elements = page.locator(selector).all()
                for element in elements:
                    try:
                        if await element.is_visible(timeout=1000):
                            await element.click()
                            await asyncio.sleep(1)
                    except:
                        continue
            except:
                continue
        
        print("   Tab cycling complete")
        
        print("7. Scrolling to load all content...")
        # Scroll more slowly with longer waits to ensure all content loads
        scroll_count = 0
        max_scrolls = 150  # Increased to 150
        scroll_step = 500  # Smaller steps for more thorough scrolling
        scroll_position = 0
        
        while scroll_count < max_scrolls:
            await page.evaluate(f"window.scrollTo(0, {scroll_position})")
            await asyncio.sleep(1.5)  # Longer wait (1.5 seconds)
            scroll_position += scroll_step
            scroll_count += 1
            
            # Get current scroll position
            current_scroll = await page.evaluate("window.pageYOffset")
            max_scroll = await page.evaluate("document.body.scrollHeight - window.innerHeight")
            
            # If we've reached the bottom, continue scrolling a bit more to be sure
            if current_scroll >= max_scroll - 100:
                print(f"   Reached bottom, doing extra scrolls to ensure all content loaded")
                # Do 15 more scrolls to be absolutely sure
                for i in range(15):
                    await page.evaluate(f"window.scrollTo(0, {scroll_position})")
                    await asyncio.sleep(1.5)
                    scroll_position += scroll_step
                break
        
        print(f"   Scrolled {scroll_count} times")
        
        print("8. Scrolling back to top...")
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(3)
        
        print("9. Getting actual content height...")
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
        
        print("10. Taking full-page screenshot...")
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
