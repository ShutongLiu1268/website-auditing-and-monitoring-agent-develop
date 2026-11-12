# Package Contents - Dell PDP Screenshot & Comparison Tools

This package contains all the code and documentation needed to capture screenshots and compare Dell Product Detail Pages across regions.

## Files to Share

### Core Scripts
1. **screenshot.py** - Main script for capturing full-page screenshots with lazy loading
2. **compare_pages.py** - Script for extracting specifications and comparing page content

### Documentation
3. **README_SCREENSHOT_TOOLS.md** - Complete usage guide with installation and customization instructions
4. **comparison_report.md** - Specification comparison table (Canada vs USA)
5. **visual_comparison.md** - Visual difference analysis with explanations

### Data Files
6. **comparison_result.json** - Full extracted data from both pages (specifications, images, pricing)

### Output Files (Generated)
7. **dell15_ca.png** - Screenshot of Canada page
8. **dell15_us.png** - Screenshot of USA page

## Quick Start for Recipients

1. Copy all files to a directory
2. Ensure Python 3.12+ is installed
3. Install dependencies:
   ```bash
   pip install playwright
   playwright install chromium
   ```
4. Run the scripts:
   ```bash
   python screenshot.py
   python compare_pages.py
   ```

## What Each File Does

| File | Purpose |
|------|---------|
| `screenshot.py` | Captures full-page screenshots with automatic cookie dismissal and lazy loading |
| `compare_pages.py` | Extracts specs, images, and pricing; creates comparison data |
| `README_SCREENSHOT_TOOLS.md` | Complete documentation for using and customizing the tools |
| `comparison_report.md` | Table showing specification differences between regions |
| `visual_comparison.md` | Analysis of visual differences with explanations |
| `comparison_result.json` | Raw extracted data for further analysis |
| `dell15_ca.png` | Example screenshot output (Canada) |
| `dell15_us.png` | Example screenshot output (USA) |

## Customization

Recipients can customize the tools by:
- Changing URLs in the `URLS` list in either script
- Adjusting wait times for slower connections
- Adding custom cookie banner selectors
- Modifying viewport size for different screen resolutions
- Changing output file names

See `README_SCREENSHOT_TOOLS.md` for detailed customization instructions.

## Notes

- The scripts use Playwright with Chromium browser
- Virtual environment is recommended but not required
- Scripts handle cookie banners and permissions automatically
- Full-page screenshots include lazy-loaded content
- Comparison highlights differences with explanations
