# Dell PDP Unified Tool - Usage Guide

## Overview

The unified tool handles both **Audits** and **Comparisons** with a simple command-line interface. Just input URLs and it handles everything automatically.

## Installation

No installation needed - it uses the existing Python environment in the backend folder.

## Usage

### For Audits

```bash
cd backend
.venv\Scripts\python.exe unified_tool.py audit <URL> [audit_type] [region]
```

**Parameters:**
- `URL` (required): The PDP URL to audit
- `audit_type` (optional): R2, R3, or Sprints/Launch (default: R2)
- `region` (optional): Country/region code (default: US)

**Examples:**
```bash
# Basic R2 audit for US
.venv\Scripts\python.exe unified_tool.py audit https://www.dell.com/en-us/shop/laptop-computers/spd/xps13dx13260

# R3 audit for Canada
.venv\Scripts\python.exe unified_tool.py audit https://www.dell.com/en-ca/shop/laptop-computers/spd/xps13dx13260 R3 CA

# Sprints/Launch audit for UK
.venv\Scripts\python.exe unified_tool.py audit https://www.dell.com/en-gb/shop/laptop-computers/spd/xps13dx13260 Sprints UK
```

**What it does:**
1. Captures full-page screenshot
2. Extracts all content (specs, images, price, full text)
3. Saves audit report as JSON
4. Saves full text for manual review

**Output files:**
- Screenshot: `us.png` or `ca.png` (based on URL)
- Content: `pdp_text.txt`
- Report: `audit_report.json`

---

### For Comparisons

```bash
cd backend
.venv\Scripts\python.exe unified_tool.py compare <URL1> <URL2>
```

**Parameters:**
- `URL1` (required): First PDP URL
- `URL2` (required): Second PDP URL

**Examples:**
```bash
# Compare Canada vs USA
.venv\Scripts\python.exe unified_tool.py compare https://www.dell.com/en-ca/shop/laptop-computers/spd/xps13dx13260 https://www.dell.com/en-us/shop/laptop-computers/spd/xps13dx13260

# Compare two different products
.venv\Scripts\python.exe unified_tool.py compare https://www.dell.com/en-us/shop/laptop-computers/spd/dell15laptopdc15250 https://www.dell.com/en-us/shop/laptop-computers/spd/dell16laptopdc16251
```

**What it does:**
1. Captures full-page screenshots of both URLs
2. Extracts content from both pages
3. Compares specifications
4. Generates comparison report
5. Shows summary of differences

**Output files:**
- Screenshots: `ca.png` and `us.png` (based on URLs)
- Report: `comparison_report.json`

---

## What You Get

### For Audits:
- ✅ Full-page screenshot
- ✅ All specifications extracted
- ✅ Price information
- ✅ Image count
- ✅ Full page text (for manual R2/R3 checkpoint review)
- ✅ JSON report with all data

### For Comparisons:
- ✅ Full-page screenshots of both pages
- ✅ Content extraction from both
- ✅ Specification comparison
- ✅ Price comparison
- ✅ Image count comparison
- ✅ JSON report with all data

---

## Process Summary

The tool automatically:

1. **Opens browser** (visible mode)
2. **Navigates to URL(s)**
3. **Dismisses cookie banners** automatically
4. **Scrolls through page** to trigger lazy loading
5. **Captures full-page screenshot**
6. **Extracts all content** (specs, images, price, text)
7. **Generates reports** with all findings

You just input the URL(s) and it does everything else!

---

## Example Output

```
============================================================
COMPARISON MODE
============================================================
URL 1: https://www.dell.com/en-ca/...
URL 2: https://www.dell.com/en-us/...

============================================================
STEP 1: Capturing Screenshots
============================================================
Processing URL 1/2: ...
   [OK] Screenshot saved to: ca.png
Processing URL 2/2: ...
   [OK] Screenshot saved to: us.png

============================================================
STEP 2: Extracting Content
============================================================
Extracting from: URL 1
   Found 26 specifications
   Found 143 images
Extracting from: URL 2
   Found 25 specifications
   Found 150 images

============================================================
STEP 3: Generating Comparison Report
============================================================
[OK] Comparison report saved to: comparison_report.json

============================================================
COMPARISON SUMMARY
============================================================
URL 1: CAD $1,049.99, 26 specs, 143 images
URL 2: $749.99, 25 specs, 150 images
Total differences: 11
```

---

## Files Location

All files are saved in the `backend` folder:
- Screenshots: `ca.png`, `us.png`, etc.
- Text content: `pdp_text.txt`
- Reports: `audit_report.json`, `comparison_report.json`

---

## Next Steps After Running

### For Audits:
1. Review `pdp_text.txt` for manual R2/R3 checkpoint review
2. Check the screenshot for visual verification
3. Use the JSON report for structured data

### For Comparisons:
1. Review both screenshots side by side
2. Check the comparison report for differences
3. Use the extracted data for further analysis

---

## Quick Reference

| Task | Command |
|------|---------|
| Audit US page | `python unified_tool.py audit <URL>` |
| Audit CA page | `python unified_tool.py audit <URL> R2 CA` |
| Compare CA vs US | `python unified_tool.py compare <CA_URL> <US_URL>` |
| Compare two products | `python unified_tool.py compare <URL1> <URL2>` |

That's it! Just input URLs and the tool handles everything automatically.
