# Prompt for Dell PDP Comparison Workflow

## Complete Prompt

You are a web scraping and comparison specialist. Your task is to compare Dell Product Detail Pages (PDPs) between Canada and USA regions. Follow this exact 3-step process:

### Step 1: Capture Full-Page Screenshots

1. Use Playwright (Python) to open both URLs in a Chromium browser
2. Configure the browser with:
   - Viewport: 1920x1080
   - Headless mode: False (visible browser)
   - Permissions: geolocation enabled
   - Ignore HTTPS errors: True
3. For each URL:
   - Navigate to the URL with wait_until="commit" and 120s timeout
   - Wait 15 seconds for initial page render
   - Automatically dismiss cookie banners by clicking buttons with text: "Accept", "Accept All", "Accept Cookies", "I Agree"
   - Scroll through the entire page to trigger lazy loading:
     - Get page height
     - Scroll in 1080px increments
     - Wait 1 second at each position
     - Detect if page height increases (more content loaded)
     - Continue until no more height increases or 50 scroll iterations
     - Scroll back to top
   - Wait 5 additional seconds for dynamic content
   - Take full-page screenshot with 120s timeout
   - Save screenshot with locale-based filename (e.g., xps13_ca.png, xps13_us.png)
4. Record: page title, final URL, page height, scroll count

### Step 2: Extract Information from Both URLs

1. Navigate to each URL (same browser configuration as Step 1)
2. Wait 10 seconds for page render
3. Dismiss cookie banners
4. Scroll through page to load all content (same scrolling logic as Step 1)
5. Extract the following information:
   - **Page Title**: Using page.title()
   - **Price**: Look for selectors: .price, [data-testid="price"], .product-price, .price-value
   - **Specifications**: Try multiple selectors (.pspecs-section, .product-specs, [data-testid="specs"], .specs-container)
     - If no specs found, extract all text from body and parse lines containing ":"
     - Extract key-value pairs where key < 50 characters
   - **Images**: Extract all <img> elements
     - Filter for images with alt text or containing "product"/"laptop" in src
     - Record src and alt attributes
   - Count total specs and images found
6. Save extracted data to JSON file

### Step 3: Compare Differences in Table Format

1. Create a comparison table with columns:
   - Specification/Element
   - Canada Value
   - USA Value
   - Difference (YES/NO)
   - Explanation (why difference exists or why no difference)
2. For each specification:
   - Compare values between Canada and USA
   - Mark as "YES" if values differ
   - Mark as "-" if values are identical
   - Provide explanation for differences (e.g., "Regional pricing", "Quebec legal requirements", "Metric vs Imperial units")
   - Provide explanation for no differences (e.g., "Same hardware specification", "Global service offering")
3. Create summary section highlighting:
   - Price differences with currency conversion notes
   - Payment options differences
   - Regional legal requirements
   - Measurement standard differences
   - Promotional offers
   - Shipping policies
   - Image count differences
4. Save comparison report as Markdown file

### Output Requirements

1. **Screenshots**: Full-page PNG files with locale-based names
2. **Extracted Data**: JSON file with all specs, images, pricing
3. **Comparison Report**: Markdown file with:
   - Overview table (title, URL, price, model, specs count, images count)
   - Detailed comparison table with explanations
   - Summary of key differences
   - Conclusion

### Example URLs Format

```python
URLS = [
    "https://www.dell.com/en-ca/shop/laptop-computers/spd/[PRODUCT_ID]",
    "https://www.dell.com/en-us/shop/laptop-computers/spd/[PRODUCT_ID]",
]
```

### Important Notes

- Always use actual extracted data, never estimate or guess prices
- Wait sufficient time for lazy-loaded content
- Handle cookie banners automatically
- Provide explanations for all differences
- Note when differences are due to regional regulations (e.g., Quebec Consumer Protection Act)
- Convert currency for price comparisons when relevant

### Error Handling

- If page load times out, continue anyway and note the error
- If cookie banner not found, continue
- If screenshot fails, check file path and permissions
- If spec extraction fails, use broader text extraction method

---

## Technical Process Documentation

### How the Sites Are Opened and Screenshots Taken

#### 1. Browser Setup
```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        permissions=["geolocation"],
        ignore_https_errors=True,
    )
    page = await context.new_page()
```

#### 2. Navigation
```python
await page.goto(url, wait_until="commit", timeout=120000)
```
- `wait_until="commit"`: Waits for navigation to commit (faster than full load)
- `timeout=120000`: 120 second timeout for slow pages

#### 3. Cookie Banner Dismissal
```python
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
            break
    except:
        continue
```

#### 4. Lazy Loading Trigger (Scrolling)
```python
page_height = await page.evaluate("document.body.scrollHeight")
scroll_position = 0
scroll_step = 1080
scroll_count = 0

while scroll_position < page_height:
    await page.evaluate(f"window.scrollTo(0, {scroll_position})")
    await asyncio.sleep(1)  # Wait for content to load
    scroll_position += scroll_step
    scroll_count += 1

    # Check if page height increased
    new_height = await page.evaluate("document.body.scrollHeight")
    if new_height > page_height:
        page_height = new_height
        print(f"Page height increased to {page_height}px")

    if scroll_count > 50:
        break

# Scroll back to top
await page.evaluate("window.scrollTo(0, 0)")
await asyncio.sleep(2)
```

#### 5. Screenshot Capture
```python
await page.screenshot(
    path=str(screenshot_path),
    full_page=True,
    timeout=120000
)
```
- `full_page=True`: Captures entire scrollable page
- `timeout=120000`: 120 second timeout for large pages

#### 6. Information Extraction
```python
# Title
title = await page.title()

# Price
price_selectors = ['.price', '[data-testid="price"]', '.product-price']
for selector in price_selectors:
    try:
        price_element = page.locator(selector).first
        if await price_element.count() > 0:
            price = await price_element.inner_text()
            break
    except:
        continue

# Specifications
spec_elements = await page.locator('.spec-item, .spec-row, li, .spec').all()
for item in spec_elements:
    text = await item.inner_text()
    if ':' in text:
        parts = text.split(':', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            if key and value:
                specs[key] = value

# Images
img_elements = await page.locator('img').all()
for img in img_elements:
    src = await img.get_attribute('src')
    alt = await img.get_attribute('alt')
    if src and (alt or 'product' in src.lower()):
        images.append({'src': src, 'alt': alt})
```

#### 7. Comparison Logic
```python
all_keys = set(ca_data['specs'].keys()) | set(us_data['specs'].keys())

for key in sorted(all_keys):
    ca_value = ca_data['specs'].get(key, 'N/A')
    us_value = us_data['specs'].get(key, 'N/A')

    if ca_value != us_value:
        diff = "YES"
    else:
        diff = ""

    table.append([key, ca_value, us_value, diff])
```

### Key Technical Details

1. **Async/Await Pattern**: All Playwright operations are asynchronous
2. **Wait Strategies**: Multiple wait types (commit, networkidle, fixed delays)
3. **Lazy Loading**: Scroll-based trigger to load dynamic content
4. **Error Handling**: Try-catch blocks for each operation
5. **File Paths**: Use absolute paths with Path objects for cross-platform compatibility
6. **Selectors**: Multiple fallback selectors for robustness
7. **Timeouts**: Generous timeouts (120s) for slow-loading pages

### Why This Approach

1. **Playwright**: Modern, reliable browser automation with good async support
2. **Visible Browser**: Allows debugging and verification
3. **Cookie Handling**: Automatic dismissal prevents blocking
4. **Lazy Loading**: Scroll trigger ensures complete page capture
5. **Multiple Selectors**: Fallback strategy handles different page layouts
6. **Full Extraction**: Captures all available data for comprehensive comparison
