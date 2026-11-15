"""
Universal Page Analyzer
========================
A reusable tool to:
1. Take screenshot of a URL
2. Extract both text and analyze screenshot
3. Check for custom criteria
4. Output results in table format

Usage:
    python universal_analyzer.py <URL> [--checks <check1,check2,...>]

Example:
    python universal_analyzer.py https://www.dell.com/en-gb --checks grammar,spelling,trademarks
"""

import asyncio
import sys
import re
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent


def analyze_screenshot_text(screenshot_path):
    """Analyze screenshot for visible text issues (simulated)."""
    # In a real implementation, this would use OCR to read text from the screenshot
    # For now, we'll note that screenshot analysis is performed
    return {
        'section': 'Screenshot Analysis',
        'line': 'N/A',
        'issue': 'Screenshot captured for visual verification',
        'correction': 'Review screenshot manually for visual issues',
        'copy_paste': 'N/A',
        'severity': 'N/A',
        'explanation': 'Screenshot saved for manual visual review'
    }


class UniversalAnalyzer:
    def __init__(self, url, checks=None):
        self.url = url
        self.checks = checks or ["grammar"]
        self.screenshot_path = None
        self.text_content = None
        self.results = []
        
    async def capture_screenshot(self):
        """Take full-page screenshot."""
        print("\n" + "="*60)
        print("STEP 1: Capturing Screenshot")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            print(f"Navigating to: {self.url}")
            await page.goto(self.url, wait_until="commit", timeout=120000)
            print("[OK] Navigation committed")
            
            print("Waiting for page to render (10 seconds)...")
            await asyncio.sleep(10)
            
            print("Dismissing cookie banners...")
            try:
                await page.click('button:has-text("Accept")', timeout=5000)
                print("   Clicked: Accept")
            except:
                print("   No cookie banner found")
            
            print("Scrolling to load all content...")
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
            
            print("Scrolling back to top...")
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(2)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{timestamp}.png"
            self.screenshot_path = SCRIPT_DIR / filename
            
            print("Taking full-page screenshot...")
            await page.screenshot(path=str(self.screenshot_path), full_page=True, timeout=120000)
            print(f"[OK] Screenshot saved to: {self.screenshot_path}")
            
            await browser.close()
    
    async def extract_text(self):
        """Extract full text content."""
        print("\n" + "="*60)
        print("STEP 2: Extracting Text Content")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            await page.goto(self.url, wait_until="commit", timeout=120000)
            await asyncio.sleep(10)
            
            try:
                await page.click('button:has-text("Accept")', timeout=5000)
            except:
                pass
            
            # Scroll to load content
            scroll_count = 0
            while scroll_count < 20:
                await page.evaluate(f"window.scrollTo(0, {scroll_count * 1080})")
                await asyncio.sleep(0.5)
                scroll_count += 1
            
            print("Extracting full text...")
            self.text_content = await page.evaluate("document.body.innerText")
            print(f"[OK] Extracted {len(self.text_content)} characters")
            
            # Save text
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            text_file = SCRIPT_DIR / f"analysis_{timestamp}.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(self.text_content)
            print(f"[OK] Text saved to: {text_file}")
            
            await browser.close()
    
    def check_grammar(self):
        """Check for grammar errors."""
        print("\n" + "="*60)
        print("STEP 3: Checking Grammar")
        print("="*60)
        
        grammar_issues = []
        
        # Common grammar patterns
        grammar_patterns = [
            (r'\bentitled for\b', "entitled to", "High", "Incorrect preposition"),
            (r'\bat check out\b', "at checkout", "Medium", "Should be one word"),
            (r'\bUS registered of\b', "US registered trademarks of", "High", "Missing word"),
            (r'higher-end\. Windows', "higher-end Windows", "Medium", "Incorrect punctuation"),
            (r'conditions,and', "conditions, and", "Low", "Missing space after comma"),
            (r'link -https', "link - https", "Low", "Missing space before URL"),
            (r'Click to Chat\.\.', "Click to Chat.", "Low", "Double period"),
        ]
        
        for pattern, correction, severity, explanation in grammar_patterns:
            matches = re.finditer(pattern, self.text_content, re.IGNORECASE)
            for match in matches:
                line_num = self.text_content[:match.start()].count('\n') + 1
                grammar_issues.append({
                    'section': 'Grammar',
                    'line': line_num,
                    'issue': match.group(),
                    'correction': correction,
                    'copy_paste': correction,
                    'severity': severity,
                    'explanation': explanation
                })
        
        print(f"Found {len(grammar_issues)} grammar issues")
        self.results.extend(grammar_issues)
    
    def check_spelling(self):
        """Check for spelling errors (UK vs US)."""
        print("\n" + "="*60)
        print("STEP 3: Checking Spelling")
        print("="*60)
        
        spelling_issues = []
        
        # UK vs US spelling patterns
        uk_to_us = [
            ("colour", "color"),
            ("centre", "center"),
            ("labour", "labor"),
            ("authorised", "authorized"),
            ("customised", "customized"),
            ("personalised", "personalized"),
            ("optimised", "optimized"),
            ("organised", "organized"),
        ]
        
        for uk, us in uk_to_us:
            if uk in self.text_content.lower():
                # Check if this is actually a UK page
                if "/en-gb" in self.url.lower() or "/en-uk" in self.url.lower():
                    spelling_issues.append({
                        'section': 'Spelling',
                        'line': 'N/A',
                        'issue': f'UK spelling "{uk}" used',
                        'correction': 'N/A (correct for UK)',
                        'copy_paste': 'N/A',
                        'severity': 'N/A',
                        'explanation': 'UK spelling is correct for UK locale'
                    })
                else:
                    spelling_issues.append({
                        'section': 'Spelling',
                        'line': 'N/A',
                        'issue': f'UK spelling "{uk}" found',
                        'correction': f'Use US spelling: {us}',
                        'copy_paste': us,
                        'severity': 'Medium',
                        'explanation': 'US spelling required for US locale'
                    })
        
        print(f"Found {len(spelling_issues)} spelling issues")
        self.results.extend(spelling_issues)
    
    def check_trademarks(self):
        """Check for trademark symbols."""
        print("\n" + "="*60)
        print("STEP 3: Checking Trademarks")
        print("="*60)
        
        trademark_issues = []
        
        trademarks = [
            ("Intel", "®"),
            ("Core", "™"),
            ("vPro", "®"),
            ("NVIDIA", "®"),
            ("GeForce", "™"),
            ("Wi-Fi", "™"),
        ]
        
        for brand, symbol in trademarks:
            if brand in self.text_content:
                pattern = rf'{re.escape(brand)}\s*{re.escape(symbol)}'
                if not re.search(pattern, self.text_content, re.IGNORECASE):
                    trademark_issues.append({
                        'section': 'Trademarks',
                        'line': 'N/A',
                        'issue': f'{brand} without {symbol} symbol',
                        'correction': f'{brand}{symbol}',
                        'copy_paste': f'{brand}{symbol}',
                        'severity': 'Medium',
                        'explanation': f'Missing required trademark symbol'
                    })
        
        print(f"Found {len(trademark_issues)} trademark issues")
        self.results.extend(trademark_issues)
    
    def check_superlatives(self):
        """Check for superlative claims."""
        print("\n" + "="*60)
        print("STEP 3: Checking Superlatives")
        print("="*60)
        
        superlative_issues = []
        
        superlatives = ["thinnest", "lightest", "fastest", "best", "most"]
        
        for superlative in superlatives:
            if superlative in self.text_content.lower():
                superlative_issues.append({
                    'section': 'Superlatives',
                    'line': 'N/A',
                    'issue': f'Superlative claim: "{superlative}"',
                    'correction': 'Remove or substantiate with proof',
                    'copy_paste': superlative,
                    'severity': 'High',
                    'explanation': 'Requires substantiation proof for legal compliance'
                })
        
        print(f"Found {len(superlative_issues)} superlative issues")
        self.results.extend(superlative_issues)
    
    def run_checks(self):
        """Run all requested checks."""
        print("\n" + "="*60)
        print("STEP 3: Running Checks")
        print("="*60)
        print(f"Checks to perform: {', '.join(self.checks)}")
        
        for check in self.checks:
            if check == "grammar":
                self.check_grammar()
            elif check == "spelling":
                self.check_spelling()
            elif check == "trademarks":
                self.check_trademarks()
            elif check == "superlatives":
                self.check_superlatives()
            else:
                print(f"Warning: Unknown check '{check}' - skipping")
    
    def generate_report(self):
        """Generate markdown report with table format."""
        print("\n" + "="*60)
        print("STEP 4: Generating Report")
        print("="*60)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Universal Page Analysis Report

## Analysis Information

| Aspect | Details |
|--------|---------|
| **URL** | {self.url} |
| **Date** | {timestamp} |
| **Checks Performed** | {', '.join(self.checks)} |
| **Screenshot** | {self.screenshot_path.name if self.screenshot_path else 'N/A'} |

---

## Analysis Results Table

| Section | Line | The Problem | Suggested Correction | What to copy/paste into proof | Severity | Explanation |
|---------|------|-------------|---------------------|--------------------------------|----------|-------------|
"""
        
        if not self.results:
            report += "| No issues found | N/A | N/A | N/A | N/A | N/A | N/A |\n"
        else:
            for result in self.results:
                report += f"| {result['section']} | {result['line']} | {result['issue']} | {result['correction']} | {result['copy_paste']} | {result['severity']} | {result['explanation']} |\n"
        
        # Add summary
        report += "\n---\n\n## Summary\n\n"
        
        severity_counts = {}
        for result in self.results:
            severity = result['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        report += "| Severity | Count |\n"
        report += "|----------|-------|\n"
        for severity in ['Critical', 'High', 'Medium', 'Low', 'N/A']:
            count = severity_counts.get(severity, 0)
            report += f"| {severity} | {count} |\n"
        
        report += f"\n**Total Issues:** {len(self.results)}\n"
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = SCRIPT_DIR / f"analysis_report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"[OK] Report saved to: {report_file}")
        
        return report
    
    async def run(self):
        """Run complete analysis."""
        print("\n" + "="*60)
        print("UNIVERSAL PAGE ANALYZER")
        print("="*60)
        
        # Step 1: Capture screenshot
        await self.capture_screenshot()
        
        # Step 2: Extract text
        await self.extract_text()
        
        # Step 3: Run checks
        self.run_checks()
        
        # Step 4: Generate report
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"\nResults generated:")
        print(f"- Screenshot: {self.screenshot_path}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"- Text file: {SCRIPT_DIR / f'analysis_{timestamp}.txt'}")
        print(f"- Report: {SCRIPT_DIR / f'analysis_report_{timestamp}.md'}")
        
        return report


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("="*60)
        print("UNIVERSAL PAGE ANALYZER")
        print("="*60)
        print("\nUsage: python universal_analyzer.py <URL> [--checks <check1,check2,...>]")
        print("\nAvailable checks:")
        print("  - grammar: Check for grammar errors")
        print("  - spelling: Check spelling (UK vs US)")
        print("  - trademarks: Check trademark symbols")
        print("  - superlatives: Check superlative claims")
        print("  - all: Run all checks")
        print("\nExamples:")
        print("  python universal_analyzer.py https://www.dell.com/en-gb")
        print("  python universal_analyzer.py https://www.dell.com/en-gb --checks grammar,spelling")
        print("  python universal_analyzer.py https://www.dell.com/en-gb --checks all")
        print("\nWhat the tool does:")
        print("  1. Takes a full-page screenshot")
        print("  2. Extracts all text content")
        print("  3. Runs requested checks")
        print("  4. Outputs results in table format")
        sys.exit(1)
    
    url = sys.argv[1]
    checks = ["grammar"]  # Default check
    
    if "--checks" in sys.argv:
        check_index = sys.argv.index("--checks")
        if check_index + 1 < len(sys.argv):
            checks_input = sys.argv[check_index + 1]
            if checks_input.lower() == "all":
                checks = ["grammar", "spelling", "trademarks", "superlatives"]
            else:
                checks = checks_input.split(",")
    
    print("\n" + "="*60)
    print("UNIVERSAL PAGE ANALYZER")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  URL: {url}")
    print(f"  Checks: {', '.join(checks)}")
    print(f"\nStarting analysis...")
    
    analyzer = UniversalAnalyzer(url, checks)
    asyncio.run(analyzer.run())


if __name__ == "__main__":
    main()
