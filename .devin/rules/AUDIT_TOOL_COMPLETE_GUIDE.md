# Website Auditing and Monitoring Tool - Complete Guide

**Version:** 1.0
**Last Updated:** 2026-11-15
**Purpose:** Comprehensive guide for website auditing and monitoring using automated screenshot capture and content analysis

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Installation & Setup](#installation--setup)
4. [Audit Types & Checkpoints](#audit-types--checkpoints)
5. [Screenshot Script (simple_screenshot.py)](#screenshot-script-simple_screenshotpy)
6. [Audit Process Methodology](#audit-process-methodology)
7. [Rules Configuration](#rules-configuration)
8. [Audit Findings Format](#audit-findings-format)
9. [Example Audit: Dell 14S Laptop](#example-audit-dell-14s-laptop)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This tool provides automated website auditing capabilities including:
- **Screenshot capture** using Playwright (headless Chromium browser)
- **Content analysis** via webfetch for text/HTML content
- **Multiple audit types**: Sprint/Launch, R2 Review, R3 Review, Accessibility testing, Page comparison
- **Regional comparison** between different country versions of pages
- **Comprehensive reporting** with severity levels and suggested fixes

### Key Features

- **Navigation-aware screenshot capture**: Automatically hides navigation menus to focus on product content
- **Multi-region support**: Handles geo-location prompts and cookie banners
- **Lazy loading support**: Scrolls through pages to ensure all content loads before capture
- **Accordion/tab expansion**: Expands collapsible sections (excluding navigation)
- **Image gallery cycling**: Clicks through product image galleries
- **Full-page screenshots**: Captures entire page content in a single image

---

## Project Structure

```
website-auditing-and-monitoring-agent-develop/
├── .devin/
│   ├── rules/
│   │   ├── always-rules.md              # Main audit rules and process
│   │   ├── page-comparison.md           # Page comparison specific rules
│   │   └── dell14s-audit-findings.md   # Example audit findings
│   └── config.json                      # Project configuration (if needed)
├── backend/
│   ├── simple_screenshot.py             # Main screenshot capture script
│   └── screenshot.py                    # Alternative multi-URL script
├── frontend/                            # Frontend application (if applicable)
└── docs/                                # Documentation
```

---

## Installation & Setup

### Prerequisites

1. **Python 3.8+** installed
2. **Playwright** and dependencies
3. **Chromium browser** (installed via Playwright)

### Installation Steps

```bash
# Install Playwright
python -m pip install playwright

# Install Chromium browser
python -m playwright install chromium

# Verify installation
python -m playwright --version
```

### Running the Screenshot Script

```bash
# Navigate to backend directory
cd backend

# Run screenshot for a single URL
python simple_screenshot.py "<URL>" <output_filename>.png

# Example
python simple_screenshot.py "https://www.dell.com/en-ca/shop/laptop-computers/spd/dell14sds14270" dell14s_ca.png
```

---

## Audit Types & Checkpoints

When auditing a URL, the agent will ask which checkpoint/framework to apply:

### 1. Sprint/Launch Audit
- Comprehensive audit covering all checkpoints
- Includes R2 and R3 requirements
- Checks tech specs and PDP for inconsistencies
- Calls out accessibility issues (WCAG/EAA compliance)

### 2. R2 Review (Sections 1-10)
- **Spelling and grammar**
- **Dimensions and weight format validation**
- **Superlatives** (best, fastest, etc.)
- **Footnotes and references**
- **Trademark verification**
- **Currency formatting**
- **Date/time formatting**
- **Technical abbreviations**
- **Capitalization consistency**
- **Formatting issues**

### 3. R3 Review (Sections 11-15)
- **Regional content differences**
- **Currency and measurement units**
- **Legal/regulatory compliance**
- **Localized terminology**
- **Regional contact information**

### 4. Accessibility Testing (WCAG 2.1/2.2 and EAA)
- **Color contrast** (4.5:1 for normal text)
- **Heading structure** (single H1, logical order)
- **Alt text on images**
- **Form labels**
- **Keyboard navigability**
- **Focus indicators**
- **Screen reader compatibility**

### 5. Page Comparison
- Requires two URLs to compare
- Compares content, specs, pricing
- Identifies regional differences
- Distinguishes expected variations from actual issues

---

## Screenshot Script (simple_screenshot.py)

### Script Overview

The `simple_screenshot.py` script uses Playwright to capture full-page screenshots of web pages with the following features:

1. **Geo-location handling**: Automatically dismisses geo-location prompts
2. **Cookie banner dismissal**: Handles common cookie consent banners
3. **Navigation hiding**: Hides navigation menus before capture
4. **Accordion expansion**: Expands collapsible sections (excluding navigation)
5. **Tab cycling**: Clicks through tabs (excluding navigation)
6. **Image gallery cycling**: Clicks through product image galleries
7. **Lazy loading support**: Scrolls through page to load all content
8. **Full-page capture**: Takes screenshot of entire page content

### Complete Script Code

```python
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
```

### Script Features Explained

1. **Headless Browser**: Launches Chromium in headless mode (can be changed to `headless=True` for background operation)
2. **Viewport**: Sets viewport to 1920x1080 for consistent screenshots
3. **Geo-location Handling**: Automatically clicks "Stay on" or "Continue to" buttons for geo-location prompts
4. **Cookie Banner Dismissal**: Handles common cookie consent banner selectors
5. **Navigation Exclusion**: Skips accordion expansion and tab cycling for navigation elements
6. **Navigation Hiding**: Uses JavaScript to hide navigation elements before screenshot
7. **Product Content Detection**: Finds main product content area to start scrolling from correct position
8. **Lazy Loading**: Scrolls through page with 1.5-second delays to ensure all content loads
9. **Full-Page Capture**: Takes screenshot of entire page content

---

## Audit Process Methodology

### Step 1: Confirm Task
Always state what task you are about to do before starting work. Briefly restate understanding of the request and confirm with the user.

### Step 2: Ask for Audit Type
When user asks to audit a URL, ask: "Which checkpoint/framework should I apply to this page?"

Options:
1. Sprint/Launch
2. R2 Review (Sections 1-10)
3. R3 Review (Sections 11-15)
4. Accessibility testing (WCAG 2.1/2.2 and EAA)
5. Page comparison (requires second URL)

### Step 3: Capture Screenshots
Use `simple_screenshot.py` to capture screenshots:
```bash
cd backend
python simple_screenshot.py "<URL>" <output_filename>.png
```

### Step 4: Fetch Page Content
Use webfetch to retrieve text/HTML content for analysis.

### Step 5: Analyze Content
Perform analysis based on selected audit type:
- **Screenshot analysis**: Visual issues, formatting, accessibility indicators
- **Text analysis**: Spelling, grammar, trademarks, dimensions, footnotes

### Step 6: Report Findings
Present findings in standard table format with columns:
- Original Problem
- Severity (Critical/High/Medium/Low)
- Issue (checkpoint violated)
- Suggested Fix
- Source (Screenshot/Webfetch)
- Original Link

---

## Rules Configuration

### always-rules.md

This file contains the main audit rules and process requirements. Key sections:

1. **Confirm task before starting**
2. **Ask which audit type and checkpoint before running**
3. **Audit process requirements** (screenshot + content analysis)
4. **Thorough screenshot analysis requirement**
5. **Audit findings table format**
6. **Accessibility testing requirements**
7. **Git and GitHub operations**

### page-comparison.md

This file contains page comparison specific rules:
- Ask for BOTH URLs before running
- Capture screenshot AND text for EACH page
- Compare side by side
- Distinguish expected regional differences from actual issues
- Present side-by-side summary table first
- Then present findings in standard table format

---

## Audit Findings Format

### Standard Findings Table

| Original Problem | Severity | Issue | Suggested Fix | Source | Original Link |
|------------------|----------|-------|---------------|--------|---------------|
| **"Customise now"** - British spelling used | Low | Spelling inconsistency | Acceptable for Canadian market | Webfetch | https://example.com |
| **Error message visible** | High | Technical issue | Fix the functionality | Screenshot | https://example.com |

### Severity Levels

- **Critical**: System-breaking issues, security vulnerabilities
- **High**: Major functionality issues, compliance violations
- **Medium**: Minor functionality issues, formatting problems
- **Low**: Typos, minor formatting, suggestions for improvement

---

## Example Audit: Dell 14S Laptop

### R2 Audit Findings (Canada Page)

**High Priority Issues:**
- "Add to Cart" functionality showing error message

**Low Priority Issues:**
- "Customise now" - British spelling (acceptable for Canada)
- "degree granting" - should be "degree-granting"
- "Wifi 6" - should be "Wi-Fi 6"
- "Type-C^{®}" - malformed trademark symbol
- Missing trademark symbols (McAfee+, Microsoft 365, Windows 11, etc.)
- "61.2 Whr" - should be "61.2 Wh"
- Date format "1/4/27" - ambiguous

### Page Comparison Findings (Canada vs USA)

**High Priority Issues:**
- "Add to Cart" error on both pages

**Medium Priority Issues:**
- Pricing differences (acceptable regional variation)
- Configuration pricing structure differences (acceptable regional variation)

**Low Priority Issues:**
- Regional spelling (Customise/Customize, Centre/Center)
- Different contact phone numbers
- Different financing programs
- Quebec regulatory content (Canada only)
- Different navigation structure
- Different social media presence

### Complete Findings Document

See `dell14s-audit-findings.md` for complete audit results including:
- R2 audit findings table
- Page comparison findings table
- Combined summary
- Action required (prioritized)
- Methodology documentation

---

## Troubleshooting

### Playwright Installation Issues

```bash
# If playwright install fails, try:
python -m pip install --upgrade pip
python -m pip install playwright

# If chromium install fails, try:
python -m playwright install chromium --with-deps
```

### Screenshot Script Issues

**Issue**: Script hangs or times out
- Increase timeout values in the script
- Check if URL is accessible
- Verify network connection

**Issue**: Navigation elements still visible in screenshot
- Add more selectors to the navigation hiding list
- Check if selectors match the site's navigation structure

**Issue**: Cookie banner not dismissed
- Add site-specific cookie banner selectors
- Increase timeout for cookie banner detection

### Webfetch Issues

**Issue**: Content truncated
- The content may be too long; read the overflow file
- Use grep to search for specific terms

**Issue**: Content not loading
- Check if URL is accessible
- Verify geo-location handling is working

---

## Best Practices

1. **Always confirm the task** before starting work
2. **Ask for audit type** before running any audit
3. **Use both screenshot and text analysis** for complete audits
4. **Hide navigation elements** to focus on product content
5. **Distinguish regional variations** from actual issues
6. **Report findings in standard table format**
7. **Prioritize issues by severity**
8. **Document methodology** for reproducibility
9. **Save audit findings** to rules folder for reference
10. **Test script on similar pages** before production use

---

## Summary

This website auditing tool provides:
- Automated screenshot capture with Playwright
- Content analysis via webfetch
- Multiple audit types (Sprint/Launch, R2, R3, Accessibility, Page Comparison)
- Navigation-aware capture (hides menus, focuses on content)
- Comprehensive reporting with severity levels
- Regional comparison capabilities
- Reproducible methodology

The tool is designed for Dell website auditing but can be adapted for any website with minor selector adjustments.

---

## Contact & Support

For issues or questions:
- Check the rules files in `.devin/rules/`
- Review the screenshot script in `backend/simple_screenshot.py`
- Refer to example findings in `dell14s-audit-findings.md`
