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
        
        print("3. Handling geo-location prompt...")
        # Handle Dell geo-location prompt - works for any region
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
        
        print("5. Expanding all accordion/toggle sections (excluding navigation)...")
        # Try to expand common accordion/toggle elements, but skip navigation
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
        
        # Navigation selectors to avoid
        nav_selectors = [
            'nav',
            '.navigation',
            '.nav-menu',
            '.header-nav',
            '.mega-menu',
            '[role="navigation"]',
            '.site-header',
            'header',
            '.top-nav',
            '.main-nav',
            '.primary-nav',
            '.dell-header',
            '.global-nav',
        ]
        
        for selector in accordion_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    try:
                        # Check if element is inside navigation
                        is_in_nav = False
                        for nav_selector in nav_selectors:
                            try:
                                nav_element = page.locator(nav_selector).first
                                if await nav_element.is_visible(timeout=500):
                                    # Check if accordion element is inside this nav
                                    is_in_nav = await element.evaluate("el => !!el.closest('nav, .navigation, .header, [role=\"navigation\"]')")
                                    if is_in_nav:
                                        break
                            except:
                                continue
                        
                        if not is_in_nav and await element.is_visible(timeout=1000):
                            await element.click()
                            await asyncio.sleep(0.5)
                    except:
                        continue
            except:
                continue
        
        print("   Accordion expansion complete (navigation skipped)")
        
        print("6. Clicking through image gallery...")
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
        
        print("7. Clicking through all tabs (excluding navigation)...")
        # Try to click through tab navigation, but skip navigation tabs
        tab_selectors = [
            '.tab-button',
            '.tab-link',
            '[role="tab"]',
            '.nav-tab',
            '.tab-item',
        ]
        
        # Navigation selectors to avoid
        nav_selectors = [
            'nav',
            '.navigation',
            '.nav-menu',
            '.header-nav',
            '.mega-menu',
            '[role="navigation"]',
            '.site-header',
            'header',
            '.top-nav',
            '.main-nav',
            '.primary-nav',
            '.dell-header',
            '.global-nav',
        ]
        
        for selector in tab_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    try:
                        # Check if element is inside navigation
                        is_in_nav = await element.evaluate("el => !!el.closest('nav, .navigation, .header, [role=\"navigation\"]')")
                        
                        if not is_in_nav and await element.is_visible(timeout=1000):
                            await element.click()
                            await asyncio.sleep(1)
                    except:
                        continue
            except:
                continue
        
        print("   Tab cycling complete (navigation skipped)")
        
        print("8. Hiding navigation elements before capturing...")
        # Hide navigation menus and header elements
        await page.evaluate("""
            () => {
                const selectors = [
                    'nav',
                    '.navigation',
                    '.nav-menu',
                    '.header-nav',
                    '.mega-menu',
                    '[role="navigation"]',
                    '.site-header',
                    'header',
                    '.top-nav',
                    '.main-nav',
                    '.primary-nav',
                    '.dell-header',
                    '.global-nav',
                    '.basket-nav',
                    '.cart-nav',
                    '.utility-nav',
                    '.menu-container',
                    '.dropdown-menu',
                    '.flyout-menu',
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
        
        print("9. Finding product content area and starting scroll position...")
        # Try to find the main product content section
        product_selectors = [
            'main',
            '.main-content',
            '[role="main"]',
            '.product-page',
            '.pdp-content',
            '#product-content',
            '.product-detail',
            '.product-showcase',
        ]
        
        product_element = None
        for selector in product_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=2000):
                    product_element = element
                    print(f"   Found product content: {selector}")
                    break
            except:
                continue
        
        if not product_element:
            print("   Could not find specific product content, using full page")
            product_element = page.locator('body')
        
        # Try to get the starting position (below navigation)
        start_position = 0
        try:
            product_bounds = await product_element.bounding_box()
            if product_bounds and product_bounds['y'] > 200:
                start_position = product_bounds['y'] - 100
                print(f"   Starting scroll from y={start_position} (below navigation)")
            else:
                print("   Starting scroll from top")
        except:
            print("   Starting scroll from top")
        
        print("10. Scrolling to load all product content...")
        # Scroll only within the product content area
        scroll_count = 0
        max_scrolls = 40
        scroll_step = 500
        scroll_position = start_position
        
        while scroll_count < max_scrolls:
            await page.evaluate(f"window.scrollTo(0, {scroll_position})")
            await asyncio.sleep(1.5)
            scroll_position += scroll_step
            scroll_count += 1
            
            # Get current scroll position
            current_scroll = await page.evaluate("window.pageYOffset")
            max_scroll = await page.evaluate("document.body.scrollHeight - window.innerHeight")
            
            # If we've reached the bottom, continue scrolling a bit more
            if current_scroll >= max_scroll - 100:
                print(f"   Reached bottom, doing extra scrolls to ensure all content loaded")
                for i in range(8):
                    await page.evaluate(f"window.scrollTo(0, {scroll_position})")
                    await asyncio.sleep(1.5)
                    scroll_position += scroll_step
                break
        
        print(f"   Scrolled {scroll_count} times")
        
        print("10. Scrolling back to top...")
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(3)
        
        print("11. Getting actual content height...")
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
        
        print("12. Taking full-page screenshot...")
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
