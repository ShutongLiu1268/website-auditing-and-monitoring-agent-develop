"""Simple script to take a screenshot using Selenium."""

import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

SCRIPT_DIR = Path(__file__).parent


def capture_screenshot(url, output_filename):
    """Capture a single page screenshot using Selenium."""
    print(f"\nCapturing screenshot of: {url}")
    print(f"Output: {output_filename}")

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    print("1. Launching Chrome browser...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        print("2. Navigating to URL...")
        driver.get(url)
        print("   [OK] Page loaded")

        print("3. Waiting for page to render (10 seconds)...")
        time.sleep(10)

        print("4. Attempting to dismiss cookie banners...")
        try:
            # Try common cookie banner selectors
            selectors = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Accept All')]",
                "//button[contains(text(), 'I Agree')]",
                "//button[contains(text(), 'Got it')]",
                "//button[@id='onetrust-accept-btn-handler']",
            ]
            for selector in selectors:
                try:
                    button = driver.find_element("xpath", selector)
                    if button.is_displayed():
                        button.click()
                        print(f"   Clicked cookie banner")
                        time.sleep(2)
                        break
                except:
                    continue
        except Exception as e:
            print(f"   No cookie banner found: {e}")

        print("5. Scrolling to load all content...")
        # Get page height
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 50

        while scroll_count < max_scrolls:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Wait for content to load

            # Calculate new scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                # Check if we're at the bottom
                if driver.execute_script("return window.innerHeight + window.pageYOffset >= document.body.scrollHeight - 100"):
                    print("   Reached bottom of page")
                    break
            last_height = new_height
            scroll_count += 1

        print(f"   Scrolled {scroll_count} times")

        print("6. Scrolling back to top...")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        print("7. Taking full-page screenshot...")
        output_path = SCRIPT_DIR / output_filename

        # Get total page height
        total_height = driver.execute_script("return document.body.scrollHeight")

        # Set window size to full page height
        driver.set_window_size(1920, total_height)

        # Take screenshot
        driver.save_screenshot(str(output_path))
        print(f"   [OK] Screenshot saved to: {output_path}")

    finally:
        print("8. Closing browser...")
        driver.quit()
        print("\nDone!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python selenium_screenshot.py <URL> <output_filename>")
        print("Example: python selenium_screenshot.py https://www.dell.com/en-gb uk_homepage.png")
        sys.exit(1)

    url = sys.argv[1]
    filename = sys.argv[2]
    capture_screenshot(url, filename)
