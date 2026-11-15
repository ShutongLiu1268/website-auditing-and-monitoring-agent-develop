"""Script to extract and compare specs and images from two Dell product pages."""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

import sys

# Get URLs from command line or use defaults
if len(sys.argv) >= 3:
    URLS = [sys.argv[1], sys.argv[2]]
else:
    URLS = [
        "https://www.dell.com/en-ca/shop/laptop-computers/spd/dell14sds14270",
        "https://www.dell.com/en-us/shop/laptop-computers/spd/dell14sds14270",
    ]

SCRIPT_DIR = Path(__file__).parent


async def extract_page_content(page, url, locale):
    """Extract specs and images from a Dell product page."""
    print(f"\n{'='*60}")
    print(f"Extracting content from {locale.upper()} page: {url}")
    print(f"{'='*60}")

    print("1. Navigating to URL...")
    await page.goto(url, wait_until="commit", timeout=120000)
    print("   [OK] Navigation committed")

    print("2. Waiting for page to render (10 seconds)...")
    await asyncio.sleep(10)

    print("3. Dismissing cookie banners...")
    cookie_selectors = [
        'button:has-text("Accept")',
        'button:has-text("Accept All")',
        'button:has-text("Accept Cookies")',
        'button:has-text("I Agree")',
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

    print("4. Scrolling to load all content...")
    page_height = await page.evaluate("document.body.scrollHeight")
    scroll_position = 0
    scroll_step = 1080
    scroll_count = 0

    while scroll_position < page_height:
        await page.evaluate(f"window.scrollTo(0, {scroll_position})")
        await asyncio.sleep(0.5)
        scroll_position += scroll_step
        scroll_count += 1
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height > page_height:
            page_height = new_height
        if scroll_count > 30:
            break

    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(2)

    print("5. Extracting page title...")
    title = await page.title()

    print("6. Extracting product specifications...")
    # Try multiple selectors for specs
    spec_selectors = [
        '.pspecs-section',
        '.product-specs',
        '[data-testid="specs"]',
        '.specs-container',
        '.specification',
        '.technical-specs',
    ]

    specs = {}
    for selector in spec_selectors:
        try:
            spec_element = page.locator(selector).first
            if await spec_element.count() > 0:
                # Extract all spec items
                spec_items = await spec_element.locator('.spec-item, .spec-row, li, .spec').all()
                for item in spec_items:
                    try:
                        text = await item.inner_text()
                        if ':' in text or '-' in text:
                            parts = text.split(':', 1) if ':' in text else text.split('-', 1)
                            if len(parts) == 2:
                                key = parts[0].strip()
                                value = parts[1].strip()
                                if key and value:
                                    specs[key] = value
                    except:
                        continue
                if specs:
                    print(f"   Found {len(specs)} specs using selector: {selector}")
                    break
        except:
            continue

    # If no specs found, try broader extraction
    if not specs:
        print("   Trying broader spec extraction...")
        try:
            all_text = await page.locator('body').inner_text()
            lines = all_text.split('\n')
            for line in lines:
                if ':' in line and len(line) < 200:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        if key and value and len(key) < 50:
                            specs[key] = value
        except:
            pass

    print("7. Extracting images...")
    images = []
    try:
        img_elements = await page.locator('img').all()
        for img in img_elements:
            try:
                src = await img.get_attribute('src')
                alt = await img.get_attribute('alt')
                if src and (alt or 'product' in src.lower() or 'laptop' in src.lower()):
                    images.append({
                        'src': src,
                        'alt': alt or 'No alt text',
                    })
            except:
                continue
        print(f"   Found {len(images)} relevant images")
    except Exception as e:
        print(f"   Error extracting images: {e}")

    print("8. Extracting price...")
    price = None
    price_selectors = [
        '.price',
        '[data-testid="price"]',
        '.product-price',
        '.price-value',
    ]
    for selector in price_selectors:
        try:
            price_element = page.locator(selector).first
            if await price_element.count() > 0:
                price = await price_element.inner_text()
                print(f"   Found price: {price}")
                break
        except:
            continue

    return {
        'locale': locale,
        'url': url,
        'title': title,
        'specs': specs,
        'images': images,
        'price': price,
    }


def create_comparison_table(ca_data, us_data):
    """Create a comparison table and highlight differences."""
    print("\n" + "="*80)
    print("COMPARISON TABLE")
    print("="*80)

    # Get all unique spec keys
    all_keys = set(ca_data['specs'].keys()) | set(us_data['specs'].keys())

    # Create table
    table = []
    table.append(["Specification", "Canada", "USA", "Difference"])

    for key in sorted(all_keys):
        ca_value = ca_data['specs'].get(key, 'N/A')
        us_value = us_data['specs'].get(key, 'N/A')

        # Check if different
        if ca_value != us_value:
            diff = "YES"
        else:
            diff = ""

        table.append([key, ca_value, us_value, diff])

    # Print table
    col_widths = [40, 40, 40, 10]
    for row in table:
        formatted_row = []
        for i, cell in enumerate(row):
            if i == 3 and cell == "YES":
                formatted_row.append(f"*** {cell} ***")
            else:
                formatted_row.append(str(cell)[:col_widths[i]-2])
        print(f"{formatted_row[0]:<40} | {formatted_row[1]:<40} | {formatted_row[2]:<40} | {formatted_row[3]:<10}")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Canada Title: {ca_data['title']}")
    print(f"USA Title: {us_data['title']}")
    print(f"Canada Price: {ca_data['price'] or 'N/A'}")
    print(f"USA Price: {us_data['price'] or 'N/A'}")
    print(f"Canada Specs: {len(ca_data['specs'])}")
    print(f"USA Specs: {len(us_data['specs'])}")
    print(f"Canada Images: {len(ca_data['images'])}")
    print(f"USA Images: {len(us_data['images'])}")

    # Count differences
    diff_count = sum(1 for row in table[1:] if row[3] == "YES")
    print(f"\nTotal Specification Differences: {diff_count}")

    # Save to JSON
    output_file = SCRIPT_DIR / "comparison_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'canada': ca_data,
            'usa': us_data,
            'comparison_table': table,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed data saved to: {output_file}")

    return table


async def main():
    print("Starting page content extraction and comparison")
    print("="*60)

    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)

        print("Creating context...")
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            permissions=["geolocation"],
            ignore_https_errors=True,
        )

        print("Creating page...")
        page = await context.new_page()

        # Extract from page(s)
        if len(URLS) == 1:
            # Single URL for R2 review
            data = await extract_page_content(page, URLS[0], "us")
            print("\n" + "="*60)
            print("EXTRACTION SUMMARY")
            print("="*60)
            print(f"Title: {data['title']}")
            print(f"URL: {data['url']}")
            print(f"Price: {data['price'] or 'N/A'}")
            print(f"Specs: {len(data['specs'])}")
            print(f"Images: {len(data['images'])}")
        else:
            # Two URLs for comparison
            ca_data = await extract_page_content(page, URLS[0], "ca")
            us_data = await extract_page_content(page, URLS[1], "us")
            # Create comparison
            create_comparison_table(ca_data, us_data)

        print("\nClosing browser...")
        await browser.close()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
