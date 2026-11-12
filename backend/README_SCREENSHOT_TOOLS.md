# Dell PDP Screenshot & Comparison Tools

A set of Python scripts using Playwright to capture screenshots of Dell Product Detail Pages (PDPs) and compare them across different regions.

## Features

- **Full-page screenshot capture** with automatic lazy loading
- **Cookie banner auto-dismissal** for uninterrupted captures
- **Multi-region comparison** (Canada vs USA, etc.)
- **Specification extraction** and comparison
- **Visual difference analysis** with explanations
- **Automatic permission handling** (geolocation, cookies, etc.)

## Prerequisites

- Python 3.12+
- Playwright and Chromium browser
- Virtual environment (recommended)

## Installation

1. Navigate to the backend directory:
```bash
cd backend
```

2. Activate the virtual environment:
```bash
.venv\Scripts\activate
```

3. Install Playwright browsers (if not already installed):
```bash
playwright install chromium
```

## Usage

### 1. Capture Screenshots

Run the screenshot script to capture full-page screenshots of URLs:

```bash
python screenshot.py
```

**What it does:**
- Opens URLs configured in the script
- Automatically dismisses cookie banners
- Scrolls through the page to trigger lazy loading
- Captures full-page screenshots
- Saves screenshots as PNG files

**Configuration:**
Edit the `URLS` list in `screenshot.py` to change which pages to capture:
```python
URLS = [
    "https://www.dell.com/en-ca/shop/laptop-computers/spd/dell15laptopdc15250",
    "https://www.dell.com/en-us/shop/laptop-computers/spd/dell15laptopdc15250",
]
```

**Output:**
- Screenshots saved as `dell15_ca.png` and `dell15_us.png` (or based on locale)
- Console output showing progress and page details

### 2. Extract and Compare Page Content

Run the comparison script to extract specifications and compare pages:

```bash
python compare_pages.py
```

**What it does:**
- Extracts product specifications from both pages
- Extracts image URLs and counts
- Extracts pricing information
- Creates a comparison table
- Saves detailed JSON data

**Output:**
- `comparison_result.json` - Full extracted data
- Console output with comparison table
- Shows differences between pages

### 3. Generate Comparison Reports

The comparison reports are generated automatically:

- `comparison_report.md` - Markdown table with specifications comparison
- `visual_comparison.md` - Visual analysis of screenshot differences

## Customization

### Change URLs

Edit the `URLS` list in either script:

```python
URLS = [
    "https://www.dell.com/en-ca/shop/laptop-computers/spd/YOUR_PRODUCT_ID",
    "https://www.dell.com/en-us/shop/laptop-computers/spd/YOUR_PRODUCT_ID",
]
```

### Adjust Wait Times

Modify these values in `screenshot.py`:

```python
# Initial render wait
await asyncio.sleep(15)

# Scroll wait per position
await asyncio.sleep(1)

# Final dynamic content wait
await asyncio.sleep(5)
```

### Change Viewport Size

Modify the browser context settings:

```python
context = await browser.new_context(
    viewport={"width": 1920, "height": 1080},  # Change resolution here
    permissions=["geolocation"],
    ignore_https_errors=True,
)
```

### Modify Cookie Banner Selectors

Add or change selectors in the cookie dismissal section:

```python
cookie_selectors = [
    'button:has-text("Accept")',
    'button:has-text("Accept All")',
    'button:has-text("Accept Cookies")',
    # Add your custom selectors here
]
```

## File Structure

```
backend/
├── screenshot.py              # Main screenshot capture script
├── compare_pages.py           # Page content extraction and comparison
├── comparison_report.md       # Specification comparison table
├── visual_comparison.md       # Visual difference analysis
├── comparison_result.json    # Full extracted data
├── dell15_ca.png             # Canada screenshot (output)
├── dell15_us.png             # USA screenshot (output)
└── README_SCREENSHOT_TOOLS.md # This file
```

## Troubleshooting

### Browser not found
```bash
playwright install chromium
```

### Timeout errors
Increase timeout values in the scripts:
```python
await page.goto(url, wait_until="commit", timeout=180000)  # Increase to 180 seconds
```

### Cookie banners not dismissed
Add custom selectors for the specific site's cookie banner.

### Screenshot incomplete
Increase scroll wait time or add more scroll iterations.

## Example Output

### Screenshot Script Output:
```
Starting comparison screenshot process for 2 URLs
============================================================
Launching Chromium browser...
Creating new browser context...
Creating new page...

Processing URL 1/2: https://www.dell.com/en-ca/...
1. Navigating to URL...
   [OK] Navigation committed
2. Waiting for page to fully render (15 seconds)...
3. Attempting to dismiss cookie banners and dialogs...
   Clicked: button:has-text("Accept")
   Dialog handling complete
4. Scrolling through page to trigger lazy loading...
   Page height increased to 16534px
   Scrolled 21 times, final height: 22274px
5. Taking full-page screenshot...
   [OK] Screenshot saved to: dell15_ca.png
```

### Comparison Script Output:
```
Starting page content extraction and comparison
============================================================
Extracting content from CA page...
Extracting product specifications...
   Found 14 specs
Extracting images...
   Found 126 relevant images
Extracting price...
   Found price: CAD $1,099.99

COMPARISON TABLE
============================================================
Specification                            | Canada                                   | USA                                      | Difference
...
Total Specification Differences: 12
```

## License

Internal tool for Dell PDP auditing and comparison.

## Support

For issues or questions, refer to the main project documentation or contact the development team.
