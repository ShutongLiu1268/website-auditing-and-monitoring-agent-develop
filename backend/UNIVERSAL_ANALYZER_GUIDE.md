# Universal Page Analyzer - Usage Guide

## What It Does

The Universal Page Analyzer automatically:
1. ✅ Takes a full-page screenshot of any URL
2. ✅ Extracts all text content from the page
3. ✅ Runs custom checks (grammar, spelling, trademarks, superlatives)
4. ✅ Generates a report in table format

## How to Use

### Basic Usage (Grammar Check Only)
```bash
cd backend
.venv\Scripts\python.exe universal_analyzer.py <URL>
```

**Example:**
```bash
.venv\Scripts\python.exe universal_analyzer.py https://www.dell.com/en-gb
```

### With Multiple Checks
```bash
.venv\Scripts\python.exe universal_analyzer.py <URL> --checks <check1,check2,...>
```

**Example:**
```bash
.venv\Scripts\python.exe universal_analyzer.py https://www.dell.com/en-gb --checks grammar,spelling,trademarks
```

## Available Checks

| Check | What It Does |
|-------|--------------|
| **grammar** | Checks for grammar errors (entitled for → entitled to, etc.) |
| **spelling** | Checks UK vs US spelling based on locale |
| **trademarks** | Checks for missing trademark symbols (Intel®, Core™, etc.) |
| **superlatives** | Checks for superlative claims (thinnest, lightest, best, etc.) |

## Output Files

After running, you'll get 3 files in the backend folder:

1. **Screenshot:** `analysis_YYYYMMDD_HHMMSS.png`
   - Full-page screenshot of the URL

2. **Text File:** `analysis_YYYYMMDD_HHMMSS.txt`
   - Complete text content extracted from the page

3. **Report:** `analysis_report_YYYYMMDD_HHMMSS.md`
   - Analysis results in table format with:
     - Section
     - Line number
     - The problem
     - Suggested correction
     - What to copy/paste into proof
     - Severity
     - Explanation

## Examples

### Check Dell UK Homepage for Grammar and Spelling
```bash
.venv\Scripts\python.exe universal_analyzer.py https://www.dell.com/en-gb --checks grammar,spelling
```

### Check Dell US Homepage for Trademarks
```bash
.venv\Scripts\python.exe universal_analyzer.py https://www.dell.com/en-us --checks trademarks
```

### Check a PDP for All Issues
```bash
.venv\Scripts\python.exe universal_analyzer.py "https://www.dell.com/en-us/shop/laptop-computers/spd/xps13dx13260" --checks grammar,spelling,trademarks,superlatives
```

## Report Format

The report includes a table like this:

| Section | Line | The Problem | Suggested Correction | What to copy/paste into proof | Severity | Explanation |
|---------|------|-------------|---------------------|--------------------------------|----------|-------------|
| Grammar | 227 | entitled for | entitled to | entitled to | High | Incorrect preposition |
| Spelling | N/A | UK spelling "colour" used | N/A (correct for UK) | N/A | N/A | UK spelling is correct for UK locale |

Plus a summary table showing severity breakdown.

## Tips

- **Always use quotes around URLs** if they contain special characters
- **Check the locale** - The spelling check automatically detects UK vs US based on URL
- **Files are timestamped** - Each run creates new files, so you won't overwrite previous results
- **All files are saved in the backend folder** for easy access

## Quick Reference

```bash
# Grammar only
python universal_analyzer.py <URL>

# Grammar + Spelling
python universal_analyzer.py <URL> --checks grammar,spelling

# All checks
python universal_analyzer.py <URL> --checks grammar,spelling,trademarks,superlatives
```

That's it! Just run the command with your URL and get instant analysis in table format.
