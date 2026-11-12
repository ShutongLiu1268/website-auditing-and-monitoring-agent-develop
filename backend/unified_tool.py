"""Unified Dell PDP Tool - Command Line Version"""

import asyncio
import sys
import json
from pathlib import Path
from playwright.async_api import async_playwright

SCRIPT_DIR = Path(__file__).parent


async def capture_screenshots(urls, locale_prefix=""):
    """Capture screenshots for given URLs."""
    print("\n" + "="*60)
    print("STEP 1: Capturing Screenshots")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            permissions=["geolocation"],
            ignore_https_errors=True,
        )
        page = await context.new_page()
        
        screenshots = []
        
        for index, url in enumerate(urls, start=1):
            print(f"\nProcessing URL {index}/{len(urls)}: {url}")
            
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
            
            print("4. Scrolling to trigger lazy loading...")
            page_height = await page.evaluate("document.body.scrollHeight")
            scroll_position = 0
            scroll_step = 1080
            scroll_count = 0
            
            while scroll_position < page_height:
                await page.evaluate(f"window.scrollTo(0, {scroll_position})")
                await asyncio.sleep(1)
                scroll_position += scroll_step
                scroll_count += 1
                
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height > page_height:
                    page_height = new_height
                    print(f"   Page height increased to {page_height}px")
                
                if scroll_count > 50:
                    print("   Reached scroll limit")
                    break
            
            print(f"   Scrolled {scroll_count} times, final height: {page_height}px")
            
            print("5. Scrolling back to top...")
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(2)
            
            print("6. Waiting for dynamic content (5 seconds)...")
            await asyncio.sleep(5)
            
            # Generate filename
            if locale_prefix:
                filename = f"{locale_prefix}.png"
            else:
                if "en-ca" in url.lower():
                    filename = "ca.png"
                elif "en-us" in url.lower():
                    filename = "us.png"
                else:
                    filename = f"page_{index}.png"
            
            screenshot_path = SCRIPT_DIR / filename
            
            print("7. Taking full-page screenshot...")
            await page.screenshot(path=str(screenshot_path), full_page=True, timeout=300000)
            print(f"   [OK] Screenshot saved to: {screenshot_path}")
            
            print("8. Getting page title...")
            title = await page.title()
            print(f"   Page title: {title}")
            
            screenshots.append({
                'url': url,
                'filename': filename,
                'path': str(screenshot_path),
                'title': title,
                'page_height': page_height,
            })
        
        await browser.close()
        print("\n[OK] All screenshots captured")
        return screenshots


async def extract_content(url):
    """Extract content from a single URL."""
    print("\n" + "="*60)
    print("STEP 2: Extracting Content")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            permissions=["geolocation"],
            ignore_https_errors=True,
        )
        page = await context.new_page()
        
        print(f"\nExtracting from: {url}")
        
        print("1. Navigating to URL...")
        await page.goto(url, wait_until="commit", timeout=120000)
        print("   [OK] Navigation committed")
        
        print("2. Waiting for page to render (10 seconds)...")
        await asyncio.sleep(10)
        
        print("3. Dismissing cookie banners...")
        try:
            element = page.locator('button:has-text("Accept")').first
            if await element.is_visible(timeout=2000):
                await element.click()
                print("   Clicked: Accept")
        except:
            pass
        
        print("4. Scrolling to load all content...")
        page_height = await page.evaluate("document.body.scrollHeight")
        scroll_position = 0
        for _ in range(30):
            await page.evaluate(f"window.scrollTo(0, {scroll_position})")
            await asyncio.sleep(0.5)
            scroll_position += 1080
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(2)
        
        print("5. Extracting page title...")
        title = await page.title()
        
        print("6. Extracting price...")
        price_selectors = ['.price', '[data-testid="price"]', '.product-price', '.price-value']
        price = None
        for selector in price_selectors:
            try:
                price_element = page.locator(selector).first
                if await price_element.count() > 0:
                    price = await price_element.inner_text()
                    print(f"   Found price: {price}")
                    break
            except:
                continue
        
        print("7. Extracting specifications...")
        all_text = await page.locator('body').inner_text()
        lines = all_text.split('\n')
        specs = {}
        for line in lines:
            if ':' in line and len(line) < 200:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key and value and len(key) < 50:
                        specs[key] = value
        
        print(f"   Found {len(specs)} specifications")
        
        print("8. Extracting images...")
        img_elements = await page.locator('img').all()
        images = []
        for img in img_elements:
            try:
                src = await img.get_attribute('src')
                alt = await img.get_attribute('alt')
                if src and (alt or 'product' in src.lower() or 'laptop' in src.lower()):
                    images.append({'src': src, 'alt': alt or 'No alt text'})
            except:
                continue
        print(f"   Found {len(images)} relevant images")
        
        print("9. Extracting full text content...")
        full_text = await page.locator('body').inner_text()
        print(f"   Extracted {len(full_text)} characters")
        
        # Save full text
        text_file = SCRIPT_DIR / "pdp_text.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"   Saved to: {text_file}")
        
        await browser.close()
        
        return {
            'title': title,
            'price': price,
            'specs': specs,
            'images': images,
            'full_text': full_text,
        }


async def run_audit(url, audit_type="R2", region="US", skip_screenshot=False):
    """Run audit workflow."""
    print("\n" + "="*60)
    print("AUDIT MODE")
    print("="*60)
    print(f"Audit Type: {audit_type}")
    print(f"Region: {region}")
    print(f"URL: {url}")
    
    # Step 1: Capture screenshot (optional)
    if skip_screenshot:
        print("\nSkipping screenshot (user requested)")
        screenshots = []
    else:
        screenshots = await capture_screenshots([url])
    
    # Step 2: Extract content
    content = await extract_content(url)
    
    # Step 3: Generate report
    print("\n" + "="*60)
    print("STEP 3: Generating Audit Report")
    print("="*60)
    
    report = {
        'audit_type': audit_type,
        'region': region,
        'url': url,
        'screenshots': screenshots,
        'content': content,
    }
    
    report_file = SCRIPT_DIR / "audit_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Audit report saved to: {report_file}")
    print("\n" + "="*60)
    print("AUDIT COMPLETE")
    print("="*60)
    print(f"\nFiles generated:")
    if screenshots:
        print(f"- Screenshot: {screenshots[0]['path']}")
    print(f"- Content: {SCRIPT_DIR / 'pdp_text.txt'}")
    print(f"- Report: {report_file}")


async def run_comparison(url1, url2):
    """Run comparison workflow."""
    print("\n" + "="*60)
    print("COMPARISON MODE")
    print("="*60)
    print(f"URL 1: {url1}")
    print(f"URL 2: {url2}")
    
    # Step 1: Capture screenshots
    screenshots = await capture_screenshots([url1, url2])
    
    # Step 2: Extract content from both
    print("\n" + "="*60)
    print("STEP 2: Extracting Content from Both Pages")
    print("="*60)
    
    content1 = await extract_content(url1)
    content2 = await extract_content(url2)
    
    # Step 3: Generate comparison report
    print("\n" + "="*60)
    print("STEP 3: Generating Comparison Report")
    print("="*60)
    
    comparison = {
        'url1': url1,
        'url2': url2,
        'content1': content1,
        'content2': content2,
        'screenshots': screenshots,
    }
    
    comparison_file = SCRIPT_DIR / "comparison_report.json"
    with open(comparison_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Comparison report saved to: {comparison_file}")
    
    # Generate comparison table
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    print(f"\nURL 1: {url1}")
    print(f"Title: {content1['title']}")
    print(f"Price: {content1['price'] or 'N/A'}")
    print(f"Specs: {len(content1['specs'])}")
    print(f"Images: {len(content1['images'])}")
    
    print(f"\nURL 2: {url2}")
    print(f"Title: {content2['title']}")
    print(f"Price: {content2['price'] or 'N/A'}")
    print(f"Specs: {len(content2['specs'])}")
    print(f"Images: {len(content2['images'])}")
    
    # Compare specs
    all_keys = set(content1['specs'].keys()) | set(content2['specs'].keys())
    diff_count = 0
    
    print("\n" + "-"*60)
    print("SPECIFICATION DIFFERENCES")
    print("-"*60)
    
    for key in sorted(all_keys):
        val1 = content1['specs'].get(key, 'N/A')
        val2 = content2['specs'].get(key, 'N/A')
        if val1 != val2:
            print(f"[DIFF] {key}:")
            print(f"  URL 1: {val1}")
            print(f"  URL 2: {val2}")
            diff_count += 1
    
    print(f"\nTotal differences: {diff_count}")
    
    print("\n" + "="*60)
    print("COMPARISON COMPLETE")
    print("="*60)
    print(f"\nFiles generated:")
    print(f"- Screenshots: {[s['path'] for s in screenshots]}")
    print(f"- Comparison report: {comparison_file}")


def main():
    """Main entry point - command line interface."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Audit: python unified_tool.py audit <URL> [audit_type] [region]")
        print("  Compare: python unified_tool.py compare <URL1> <URL2>")
        print("\nExamples:")
        print("  python unified_tool.py audit https://www.dell.com/en-us/shop/laptop-computers/spd/xps13dx13260 R2 US")
        print("  python unified_tool.py compare https://www.dell.com/en-ca/shop/laptop-computers/spd/xps13dx13260 https://www.dell.com/en-us/shop/laptop-computers/spd/xps13dx13260")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == "audit":
        url = sys.argv[2]
        audit_type = sys.argv[3] if len(sys.argv) > 3 else "R2"
        region = sys.argv[4] if len(sys.argv) > 4 else "US"
        asyncio.run(run_audit(url, audit_type, region))
    
    elif mode == "compare":
        url1 = sys.argv[2]
        url2 = sys.argv[3]
        asyncio.run(run_comparison(url1, url2))
    
    else:
        print(f"Unknown mode: {mode}")
        print("Use 'audit' or 'compare'")


if __name__ == "__main__":
    main()
