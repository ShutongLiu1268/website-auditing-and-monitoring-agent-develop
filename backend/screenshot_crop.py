"""Take screenshot and automatically crop empty whitespace."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image
import numpy as np

SCRIPT_DIR = Path(__file__).parent


async def capture_and_crop_screenshot(url, output_filename):
    """Capture screenshot and crop empty whitespace."""
    print(f"\nCapturing and cropping: {url}")
    
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
            print("   No cookie banner found")
        
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
        
        print("5. Scrolling back to top...")
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(2)
        
        print("6. Taking full-page screenshot...")
        temp_path = SCRIPT_DIR / "temp_screenshot.png"
        await page.screenshot(path=str(temp_path), full_page=True, timeout=120000)
        print(f"   [OK] Screenshot saved to: {temp_path}")
        
        await browser.close()
    
    # Crop whitespace
    print("7. Cropping empty whitespace...")
    img = Image.open(temp_path)
    
    # Convert to numpy array for processing
    img_array = np.array(img)
    
    # Find top boundary (first non-white row)
    top = 0
    for y in range(img_array.shape[0]):
        row = img_array[y]
        # Check if row is not all white (or near white)
        if not np.all(row > 250):
            top = y
            break
    
    # Find bottom boundary (last non-white row)
    bottom = img_array.shape[0]
    for y in range(img_array.shape[0] - 1, -1, -1):
        row = img_array[y]
        if not np.all(row > 250):
            bottom = y + 1
            break
    
    # Crop the image
    cropped = img.crop((0, top, img.width, bottom))
    
    # Save cropped image
    output_path = SCRIPT_DIR / output_filename
    cropped.save(output_path)
    print(f"   [OK] Cropped screenshot saved to: {output_path}")
    
    # Delete temp file
    temp_path.unlink()
    
    print(f"\nOriginal size: {img.size}")
    print(f"Cropped size: {cropped.size}")
    print(f"Removed: {img.height - cropped.height}px of whitespace")
    
    print("\nDone!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python screenshot_crop.py <URL> <output_filename>")
        sys.exit(1)
    
    url = sys.argv[1]
    filename = sys.argv[2]
    asyncio.run(capture_and_crop_screenshot(url, filename))
