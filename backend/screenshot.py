"""Script to open two URLs, take screenshots, and compare them."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

URLS = [
    "https://www.dell.com/en-us/shop/laptop-computers/spd/xps13dx13260#configure-anchor",
]
SCRIPT_DIR = Path(__file__).parent


async def capture_page(page, url, index, total):
    """Capture a single page screenshot."""
    print(f"\n{'='*60}")
    print(f"Processing URL {index}/{total}: {url}")
    print(f"{'='*60}")

    print(f"1. Navigating to URL...")
    try:
        await page.goto(url, wait_until="commit", timeout=120000)
        print("   [OK] Navigation committed")
    except Exception as e:
        print(f"   [WARN] Page load issue: {e}")
        print("   Continuing anyway...")

    print("2. Waiting for page to fully render (15 seconds)...")
    await asyncio.sleep(15)

    print("3. Attempting to dismiss cookie banners and dialogs...")
    # Try to click common cookie banner buttons
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

    print("   Dialog handling complete")

    print("4. Scrolling through page to trigger lazy loading...")
    # Get page height
    page_height = await page.evaluate("document.body.scrollHeight")
    viewport_height = 1080

    # Scroll through the page in chunks
    scroll_position = 0
    scroll_step = viewport_height
    scroll_count = 0

    while scroll_position < page_height:
        await page.evaluate(f"window.scrollTo(0, {scroll_position})")
        await asyncio.sleep(1)  # Wait for content to load
        scroll_position += scroll_step
        scroll_count += 1

        # Check if page height increased (more content loaded)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height > page_height:
            page_height = new_height
            print(f"   Page height increased to {page_height}px")

        # Safety limit
        if scroll_count > 50:
            print("   Reached scroll limit, stopping")
            break

    print(f"   Scrolled {scroll_count} times, final height: {page_height}px")

    # Scroll back to top
    print("5. Scrolling back to top...")
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(2)

    print("6. Additional wait for dynamic content (5 seconds)...")
    await asyncio.sleep(5)

    # Generate filename based on URL
    locale = "ca" if "en-ca" in url else "us"
    screenshot_path = SCRIPT_DIR / f"xps13_{locale}.png"

    print("7. Taking full-page screenshot...")
    await page.screenshot(path=str(screenshot_path), full_page=True, timeout=120000)
    print(f"   [OK] Screenshot saved to: {screenshot_path}")

    print("8. Getting page title...")
    title = await page.title()
    print(f"   Page title: {title}")

    print("9. Getting page URL (after redirects)...")
    final_url = page.url
    print(f"   Final URL: {final_url}")

    return {
        "url": url,
        "final_url": final_url,
        "title": title,
        "screenshot": str(screenshot_path),
    }


async def main():
    print(f"Starting comparison screenshot process for {len(URLS)} URLs")
    print("=" * 60)

    async with async_playwright() as p:
        print("Launching Chromium browser...")
        browser = await p.chromium.launch(headless=False)

        print("Creating new browser context...")
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            # Automatically grant common permissions
            permissions=["geolocation"],
            # Accept cookies automatically
            accept_downloads=True,
            # Ignore HTTPS errors
            ignore_https_errors=True,
        )

        print("Creating new page...")
        page = await context.new_page()

        results = []
        for index, url in enumerate(URLS, start=1):
            result = await capture_page(page, url, index, len(URLS))
            results.append(result)

        print("\n" + "=" * 60)
        print("COMPARISON SUMMARY")
        print("=" * 60)

        for i, result in enumerate(results, start=1):
            print(f"\nURL {i}:")
            print(f"  Original: {result['url']}")
            print(f"  Final:    {result['final_url']}")
            print(f"  Title:    {result['title']}")
            print(f"  Screenshot: {result['screenshot']}")

        print("\n" + "=" * 60)
        print("Comparison complete!")
        print(f"Total screenshots: {len(results)}")

        print("\nKeeping browser open for 5 seconds for inspection...")
        await asyncio.sleep(5)

        print("Closing browser...")
        await browser.close()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
