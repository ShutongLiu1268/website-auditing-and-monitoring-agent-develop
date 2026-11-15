"""
Universal Page Analyzer V2
========================
A comprehensive tool to:
1. Take screenshot of a URL
2. Extract both text and analyze screenshot
3. Check for custom criteria (R2, R3, Compare, Accessibility)
4. Output results in table format

Usage:
    python universal_analyzer_v2.py <URL> --audit-type <type>

Audit Types:
    - r2: R2 Review (Global English) - Sections 1-10
    - r3: R3 Review (Regional) - Sections 11-15
    - compare: Compare two pages
    - accessibility: WCAG and EAA accessibility checks
    - links: Check for broken links
    - all: Run all audit types

Example:
    python universal_analyzer_v2.py https://www.dell.com/en-gb --audit-type r2
"""

import asyncio
import sys
import re
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
SCREENSHOTS_DIR = SCRIPT_DIR / "screenshots"
REPORTS_DIR = SCRIPT_DIR / "reports"

# Create folders if they don't exist
SCREENSHOTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


class UniversalAnalyzerV2:
    def __init__(self, url, audit_type="r2", region="US"):
        self.url = url
        self.audit_type = audit_type
        self.region = region
        self.screenshot_path = None
        self.text_content = None
        self.results = []
        
    async def capture_screenshot_and_text(self):
        """Take full-page screenshot and extract text in one pass."""
        print("\n" + "="*60)
        print("STEP 1: Capturing Screenshot and Extracting Text")
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
            
            # Generate descriptive filename from URL
            url_parts = self.url.replace("https://", "").replace("http://", "").split("/")
            page_name = url_parts[1] if len(url_parts) > 1 else "page"
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"{page_name}_{self.region}_{date_str}.png"
            self.screenshot_path = SCREENSHOTS_DIR / filename
            
            print("Taking full-page screenshot...")
            await page.screenshot(path=str(self.screenshot_path), full_page=True, timeout=120000)
            print(f"[OK] Screenshot saved to: {self.screenshot_path}")
            
            print("Extracting full text...")
            self.text_content = await page.evaluate("document.body.innerText")
            print(f"[OK] Extracted {len(self.text_content)} characters")
            
            # Save text
            text_filename = f"{page_name}_{self.region}_{date_str}.txt"
            text_file = REPORTS_DIR / text_filename
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(self.text_content)
            print(f"[OK] Text saved to: {text_file}")
            
            await browser.close()
    
    def check_r2_section1_spelling(self):
        """Section 1 - Spelling Check (UK vs US English)."""
        print("\n" + "="*60)
        print("R2 SECTION 1: Spelling Check")
        print("="*60)
        
        issues = []
        
        # UK English regions
        uk_regions = ["UK", "IE", "AU", "NZ", "MY", "SG", "IN", "HK"]
        # US English regions
        us_regions = ["PH", "PK", "TH", "VN", "ID", "US"]
        
        # US vs UK spelling variations
        spelling_variations = [
            ("gray", "grey"),
            ("maneuver", "manoeuvre"),
            ("center", "centre"),
            ("fiber", "fibre"),
            ("liter", "litre"),
            ("actualize", "actualise"),
            ("analyze", "analyse"),
            ("apologize", "apologise"),
            ("civilize", "civilise"),
            ("customizable", "customisable"),
            ("customization", "customisation"),
            ("customize", "customise"),
            ("maximize", "maximise"),
            ("minimize", "minimise"),
            ("modernize", "modernise"),
            ("optimization", "optimisation"),
            ("optimize", "optimise"),
            ("optimized", "optimised"),
            ("organization", "organisation"),
            ("organized", "organised"),
            ("personalize", "personalise"),
            ("prioritize", "prioritise"),
            ("recognize", "recognise"),
            ("synchronize", "synchronise"),
            ("stabilization", "stabilisation"),
            ("stabilize", "stabilise"),
            ("stabilized", "stabilised"),
            ("canceled", "cancelled"),
            ("fueled", "fuelled"),
            ("fueling", "fuelling"),
            ("labeled", "labelled"),
            ("modeled", "modelled"),
            ("modeling", "modelling"),
            ("rivaled", "rivalled"),
            ("rivaling", "rivalling"),
            ("traveled", "travelled"),
            ("traveling", "travelling"),
            ("traveler", "traveller"),
            ("catalog", "catalogue"),
            ("analog", "analogue"),
            ("color", "colour"),
            ("flavor", "flavour"),
            ("favorite", "favourite"),
            ("humor", "humour"),
            ("labor", "labour"),
            ("neighbor", "neighbour"),
            ("defense", "defence"),
            ("license", "licence"),
            ("offense", "offence"),
            ("pretense", "pretence"),
            ("aluminum", "aluminium"),
        ]
        
        for us_spelling, uk_spelling in spelling_variations:
            if self.region in uk_regions:
                # Should use UK spelling
                if us_spelling.lower() in self.text_content.lower():
                    issues.append({
                        'section': 'Section 1 - Spelling',
                        'line': 'N/A',
                        'issue': f'US spelling "{us_spelling}" found (should use UK spelling)',
                        'correction': f'Use UK spelling: {uk_spelling}',
                        'copy_paste': uk_spelling,
                        'severity': 'High',
                        'explanation': f'UK English required for {self.region} region'
                    })
            elif self.region in us_regions:
                # Should use US spelling
                if uk_spelling.lower() in self.text_content.lower():
                    issues.append({
                        'section': 'Section 1 - Spelling',
                        'line': 'N/A',
                        'issue': f'UK spelling "{uk_spelling}" found (should use US spelling)',
                        'correction': f'Use US spelling: {us_spelling}',
                        'copy_paste': us_spelling,
                        'severity': 'High',
                        'explanation': f'US English required for {self.region} region'
                    })
        
        print(f"Found {len(issues)} spelling issues")
        self.results.extend(issues)
    
    def check_r2_section2_spelling_errors(self):
        """Section 2 - Spelling Errors & Language Mismatch."""
        print("\n" + "="*60)
        print("R2 SECTION 2: Spelling Errors & Language Mismatch")
        print("="*60)
        
        issues = []
        
        # Common spelling errors
        spelling_errors = [
            (r'\bteh\b', 'the'),
            (r'\bwoudl\b', 'would'),
            (r'\bcoudl\b', 'could'),
            (r'\bshoudl\b', 'should'),
            (r'\brecieve\b', 'receive'),
            (r'\boccured\b', 'occurred'),
            (r'\bseperate\b', 'separate'),
            (r'\bdefinately\b', 'definitely'),
            (r'\bgoverment\b', 'government'),
            (r'\boccassion\b', 'occasion'),
        ]
        
        for error, correction in spelling_errors:
            matches = re.finditer(error, self.text_content, re.IGNORECASE)
            for match in matches:
                line_num = self.text_content[:match.start()].count('\n') + 1
                issues.append({
                    'section': 'Section 2 - Spelling Errors',
                    'line': line_num,
                    'issue': match.group(),
                    'correction': correction,
                    'copy_paste': correction,
                    'severity': 'High',
                    'explanation': 'Spelling error detected'
                })
        
        print(f"Found {len(issues)} spelling errors")
        self.results.extend(issues)
    
    def check_r2_section3_dimensions(self):
        """Section 3 - Weight & Dimension Format Check."""
        print("\n" + "="*60)
        print("R2 SECTION 3: Weight & Dimension Format Check")
        print("="*60)
        
        issues = []
        
        # Check for inch format issues
        if '"' in self.text_content and 'inch' not in self.text_content.lower():
            issues.append({
                'section': 'Section 3 - Dimensions',
                'line': 'N/A',
                'issue': 'Using " symbol instead of "inch"',
                'correction': 'Use "inch" instead of " symbol',
                'copy_paste': 'inch',
                'severity': 'Medium',
                'explanation': 'Should spell out "inch" in content descriptions'
            })
        
        # Check for dimension format (mm first, inches in brackets for most regions)
        if self.region in ["UK", "IE", "CH", "BE", "AT", "NL", "ES", "IT", "NO", "DK", "SE", "AU", "NZ", "MY", "SG"]:
            # Should show mm first, inches in brackets
            if re.search(r'\d+\s*inches?\s*\(', self.text_content, re.IGNORECASE):
                issues.append({
                    'section': 'Section 3 - Dimensions',
                    'line': 'N/A',
                    'issue': 'Inches shown before mm',
                    'correction': 'Show mm first, inches in brackets',
                    'copy_paste': 'mm (inches)',
                    'severity': 'Medium',
                    'explanation': f'{self.region} requires mm first, inches in brackets'
                })
        
        print(f"Found {len(issues)} dimension format issues")
        self.results.extend(issues)
    
    def check_r2_section6_superlatives(self):
        """Section 6 - Unsupported Superlative Claims."""
        print("\n" + "="*60)
        print("R2 SECTION 6: Superlative Claims")
        print("="*60)
        
        issues = []
        
        # Countries avoiding "World's x" superlative claims
        countries_avoiding = ["UK", "IE", "FR", "CH", "BE", "DE", "AT", "NL", "ES", "IT", "NO", "DK", "SE", "AU", "NZ", "MY", "SG", "PH", "VN", "TH", "KR", "CN", "HK", "TW"]
        
        superlatives = ["most", "the most", "thinnest", "lightest", "fastest", "best", "world's"]
        
        if self.region in countries_avoiding:
            for superlative in superlatives:
                if superlative.lower() in self.text_content.lower():
                    issues.append({
                        'section': 'Section 6 - Superlatives',
                        'line': 'N/A',
                        'issue': f'Superlative claim: "{superlative}"',
                        'correction': 'Remove or substantiate with proof',
                        'copy_paste': superlative,
                        'severity': 'High',
                        'explanation': f'{self.region} avoids superlative claims without substantiation'
                    })
        
        print(f"Found {len(issues)} superlative issues")
        self.results.extend(issues)
    
    def check_r2_section7_footnotes(self):
        """Section 7 - Tech Note Functionality."""
        print("\n" + "="*60)
        print("R2 SECTION 7: Footnote References")
        print("="*60)
        
        issues = []
        
        # Find footnote references
        footnote_refs = re.findall(r'\[?\d+\]?', self.text_content)
        
        # Check if footnote explanations exist
        for ref in set(footnote_refs):
            if ref not in self.text_content:
                issues.append({
                    'section': 'Section 7 - Footnotes',
                    'line': 'N/A',
                    'issue': f'Footnote reference {ref} missing explanation',
                    'correction': 'Add footnote explanation',
                    'copy_paste': 'Add explanation',
                    'severity': 'Medium',
                    'explanation': 'Footnote reference without matching explanation'
                })
        
        print(f"Found {len(issues)} footnote issues")
        self.results.extend(issues)
    
    def check_r2_section8_copilot(self):
        """Section 8 - CN Locale No Copilot."""
        print("\n" + "="*60)
        print("R2 SECTION 8: CN Locale - Copilot Check")
        print("="*60)
        
        issues = []
        
        if self.region == "CN":
            if "copilot" in self.text_content.lower():
                issues.append({
                    'section': 'Section 8 - CN Locale',
                    'line': 'N/A',
                    'issue': 'Copilot references found',
                    'correction': 'Remove Copilot references',
                    'copy_paste': 'Remove Copilot',
                    'severity': 'Critical',
                    'explanation': 'CN PDPs must not contain Copilot references'
                })
        
        print(f"Found {len(issues)} Copilot issues")
        self.results.extend(issues)
    
    def check_r2_section9_trademarks(self):
        """Section 9 - Trademark (™ / ®) Accuracy."""
        print("\n" + "="*60)
        print("R2 SECTION 9: Trademark Symbols")
        print("="*60)
        
        issues = []
        
        trademarks = [
            ("Intel", "®"),
            ("vPro", "®"),
            ("NVIDIA", "®"),
            ("Qualcomm", "®"),
            ("Core", "™"),
            ("Arc", "™"),
            ("GeForce RTX", "™"),
            ("Ryzen", "™"),
            ("Adreno", "™"),
        ]
        
        for brand, symbol in trademarks:
            if brand in self.text_content:
                pattern = rf'{re.escape(brand)}\s*{re.escape(symbol)}'
                if not re.search(pattern, self.text_content, re.IGNORECASE):
                    issues.append({
                        'section': 'Section 9 - Trademarks',
                        'line': 'N/A',
                        'issue': f'{brand} without {symbol} symbol',
                        'correction': f'{brand}{symbol}',
                        'copy_paste': f'{brand}{symbol}',
                        'severity': 'Medium',
                        'explanation': f'Missing required trademark symbol'
                    })
        
        print(f"Found {len(issues)} trademark issues")
        self.results.extend(issues)
    
    def check_r2_section10_peace_of_mind(self):
        """Section 10 - Peace of Mind Module."""
        print("\n" + "="*60)
        print("R2 SECTION 10: Peace of Mind Module")
        print("="*60)
        
        issues = []
        
        # APJC regions should not have Peace of Mind module
        apjc_regions = ["JP", "KR", "CN", "TW", "HK", "SG", "MY", "TH", "VN", "ID", "PH", "PK", "IN", "AU", "NZ"]
        
        if self.region in apjc_regions:
            if "peace of mind" in self.text_content.lower():
                issues.append({
                    'section': 'Section 10 - Peace of Mind',
                    'line': 'N/A',
                    'issue': 'Peace of Mind module found',
                    'correction': 'Remove Peace of Mind module',
                    'copy_paste': 'Remove module',
                    'severity': 'High',
                    'explanation': f'Peace of Mind module should be removed for {self.region}'
                })
        
        print(f"Found {len(issues)} Peace of Mind issues")
        self.results.extend(issues)
    
    def check_r3_sections(self):
        """R3 Review - Sections 11-15 (Regional Reviews)."""
        print("\n" + "="*60)
        print("R3 REVIEW: Regional Content Check")
        print("="*60)
        
        issues = []
        
        # Section 11-15 require native speaker review
        # For automated checks, we can flag potential issues
        
        # Check for English words on non-English pages
        if self.region not in ["US", "UK", "IE", "AU", "NZ", "CA"]:
            # This is a non-English region
            # Flag for native speaker review
            issues.append({
                'section': 'R3 - Section 11-15',
                'line': 'N/A',
                'issue': 'Regional content requires native speaker review',
                'correction': 'Review with native speaker',
                'copy_paste': 'N/A',
                'severity': 'Medium',
                'explanation': 'Sections 11-15 require native speaker review for meaning, tone, naturalness, accents, and localization'
            })
        
        print(f"Found {len(issues)} R3 issues")
        self.results.extend(issues)
    
    def check_accessibility_wcag(self):
        """Accessibility Check - WCAG and EAA compliance."""
        print("\n" + "="*60)
        print("ACCESSIBILITY: WCAG and EAA Compliance")
        print("="*60)
        
        issues = []
        
        # WCAG 2.1 Level A and AA checks
        
        # 1. Alt text for images
        if '<img' in self.text_content and 'alt=' not in self.text_content:
            issues.append({
                'section': 'Accessibility - WCAG',
                'line': 'N/A',
                'issue': 'Images may be missing alt text',
                'correction': 'Add alt text to all images',
                'copy_paste': 'Add alt=""',
                'severity': 'High',
                'explanation': 'WCAG 1.1.1 - Non-text content must have text alternatives'
            })
        
        # 2. Color contrast (can't check without actual page, flag for review)
        issues.append({
            'section': 'Accessibility - WCAG',
            'line': 'N/A',
            'issue': 'Color contrast should be reviewed manually',
            'correction': 'Ensure 4.5:1 contrast ratio for text',
            'copy_paste': 'Check contrast',
            'severity': 'Medium',
            'explanation': 'WCAG 1.4.3 - Minimum contrast ratio 4.5:1 for normal text'
        })
        
        # 3. Form labels
        if '<input' in self.text_content and 'label' not in self.text_content:
            issues.append({
                'section': 'Accessibility - WCAG',
                'line': 'N/A',
                'issue': 'Form inputs may be missing labels',
                'correction': 'Add labels to all form inputs',
                'copy_paste': 'Add <label>',
                'severity': 'High',
                'explanation': 'WCAG 1.3.1 - Information and relationships must be programmatically determinable'
            })
        
        # 4. Heading structure
        if '<h1>' not in self.text_content:
            issues.append({
                'section': 'Accessibility - WCAG',
                'line': 'N/A',
                'issue': 'Missing H1 heading',
                'correction': 'Add H1 heading to page',
                'copy_paste': 'Add <h1>',
                'severity': 'High',
                'explanation': 'WCAG 1.3.1 - Pages must have proper heading structure'
            })
        
        # 5. Link text
        if 'click here' in self.text_content.lower() or 'read more' in self.text_content.lower():
            issues.append({
                'section': 'Accessibility - WCAG',
                'line': 'N/A',
                'issue': 'Non-descriptive link text found',
                'correction': 'Use descriptive link text',
                'copy_paste': 'Update link text',
                'severity': 'Medium',
                'explanation': 'WCAG 2.4.4 - Link purpose should be clear from link text alone'
            })
        
        # 6. EAA - European Accessibility Act specific checks
        if self.region in ["FR", "DE", "IT", "ES", "NL", "BE", "AT", "CH"]:
            issues.append({
                'section': 'Accessibility - EAA',
                'line': 'N/A',
                'issue': 'EAA compliance review required',
                'correction': 'Ensure full EAA compliance',
                'copy_paste': 'Review EAA',
                'severity': 'High',
                'explanation': 'European Accessibility Act requires accessibility compliance for digital products'
            })
        
        print(f"Found {len(issues)} accessibility issues")
        self.results.extend(issues)
    
    async def check_broken_links(self):
        """Check for broken links on the page."""
        print("\n" + "="*60)
        print("BROKEN LINKS CHECK")
        print("="*60)
        
        try:
            import aiohttp
            from urllib.parse import urljoin
        except ImportError:
            print("aiohttp not installed - skipping broken link check")
            print("Install with: pip install aiohttp")
            return
        
        issues = []
        
        # Extract links from the page using Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.goto(self.url, wait_until="commit", timeout=120000)
            await asyncio.sleep(5)
            
            # Get all links
            links = await page.eval_on_selector_all('a[href]', 'elements => elements.map(e => e.href)')
            
            await browser.close()
        
        if not links:
            print("No links found on page")
            return
        
        print(f"Found {len(links)} links, checking...")
        
        # Check each link
        checked_count = 0
        max_checks = 50  # Limit to avoid timeout
        
        for link in links[:max_checks]:
            try:
                # Skip javascript: and mailto: links
                if link.startswith('javascript:') or link.startswith('mailto:') or link.startswith('#'):
                    continue
                
                # Make absolute URL
                absolute_url = urljoin(self.url, link)
                
                # Skip non-http links
                if not absolute_url.startswith(('http://', 'https://')):
                    continue
                
                # Check link status
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    try:
                        async with session.head(absolute_url, allow_redirects=True) as response:
                            if response.status >= 400:
                                issues.append({
                                    'section': 'Broken Links',
                                    'line': 'N/A',
                                    'issue': f'Broken link: {absolute_url}',
                                    'correction': 'Fix or remove broken link',
                                    'copy_paste': absolute_url,
                                    'severity': 'High',
                                    'explanation': f'HTTP {response.status} - Link returns error'
                                })
                    except Exception as e:
                        issues.append({
                            'section': 'Broken Links',
                            'line': 'N/A',
                            'issue': f'Broken link: {absolute_url}',
                            'correction': 'Fix or remove broken link',
                            'copy_paste': absolute_url,
                            'severity': 'High',
                            'explanation': f'Connection error: {str(e)}'
                        })
                
                checked_count += 1
                if checked_count % 10 == 0:
                    print(f"   Checked {checked_count}/{min(len(links), max_checks)} links...")
            
            except Exception as e:
                print(f"   Error checking link: {e}")
        
        print(f"Checked {checked_count} links, found {len(issues)} broken links")
        self.results.extend(issues)
    
    async def run_audit(self):
        """Run the requested audit type."""
        print("\n" + "="*60)
        print(f"STEP 3: Running {self.audit_type.upper()} Audit")
        print("="*60)
        
        if self.audit_type == "r2" or self.audit_type == "all":
            print("\n--- Running R2 Review (Sections 1-10) ---")
            self.check_r2_section1_spelling()
            self.check_r2_section2_spelling_errors()
            self.check_r2_section3_dimensions()
            self.check_r2_section6_superlatives()
            self.check_r2_section7_footnotes()
            self.check_r2_section8_copilot()
            self.check_r2_section9_trademarks()
            self.check_r2_section10_peace_of_mind()
        
        if self.audit_type == "r3" or self.audit_type == "all":
            print("\n--- Running R3 Review (Sections 11-15) ---")
            self.check_r3_sections()
        
        if self.audit_type == "accessibility" or self.audit_type == "all":
            print("\n--- Running Accessibility (WCAG/EAA) Check ---")
            self.check_accessibility_wcag()
        
        if self.audit_type == "links" or self.audit_type == "all":
            print("\n--- Running Broken Links Check ---")
            await self.check_broken_links()
        
        if self.audit_type == "compare":
            print("\n--- Compare mode requires two URLs ---")
            print("Use the compare_pages.py script for comparison")
    
    def generate_report(self):
        """Generate markdown report with table format."""
        print("\n" + "="*60)
        print("STEP 4: Generating Report")
        print("="*60)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Universal Page Analysis Report

## Analysis Information

|| Aspect | Details |
||--------|---------|
|| **URL** | {self.url} |
|| **Date** | {timestamp} |
|| **Audit Type** | {self.audit_type.upper()} |
|| **Region** | {self.region} |
|| **Screenshot** | {self.screenshot_path.name if self.screenshot_path else 'N/A'} |

---

## Analysis Results Table

|| Section | The Problem | Suggested Correction | What to copy/paste into proof | Severity | Explanation |
||---------|------|-------------|---------------------|--------------------------------|----------|-------------|
"""
        
        if not self.results:
            report += "| No issues found | N/A | N/A | N/A | N/A | N/A |\n"
        else:
            for result in self.results:
                report += f"| {result['section']} | {result['issue']} | {result['correction']} | {result['copy_paste']} | {result['severity']} | {result['explanation']} |\n"
        
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
        
        # Save report with descriptive name
        url_parts = self.url.replace("https://", "").replace("http://", "").split("/")
        page_name = url_parts[1] if len(url_parts) > 1 else "page"
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_filename = f"{page_name}_{self.region}_{self.audit_type}_{date_str}.md"
        report_file = REPORTS_DIR / report_filename
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"[OK] Report saved to: {report_file}")
        
        return report
    
    async def run(self):
        """Run complete analysis."""
        print("\n" + "="*60)
        print("UNIVERSAL PAGE ANALYZER V2")
        print("="*60)
        print(f"\nAudit Type: {self.audit_type.upper()}")
        print(f"Region: {self.region}")
        
        # Step 1: Capture screenshot and extract text in one pass
        await self.capture_screenshot_and_text()
        
        # Step 2: Run audit (some checks are async)
        await self.run_audit()
        
        # Step 3: Generate report
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"\nResults generated:")
        print(f"- Screenshot: {self.screenshot_path}")
        url_parts = self.url.replace("https://", "").replace("http://", "").split("/")
        page_name = url_parts[1] if len(url_parts) > 1 else "page"
        date_str = datetime.now().strftime("%Y-%m-%d")
        print(f"- Text file: {REPORTS_DIR / f'{page_name}_{self.region}_{date_str}.txt'}")
        print(f"- Report: {REPORTS_DIR / f'{page_name}_{self.region}_{self.audit_type}_{date_str}.md'}")
        
        return report


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("="*60)
        print("UNIVERSAL PAGE ANALYZER V2")
        print("="*60)
        print("\nUsage: python universal_analyzer_v2.py <URL> --audit-type <type> --region <region>")
        print("\nAudit Types:")
        print("  - r2: R2 Review (Global English) - Sections 1-10")
        print("  - r3: R3 Review (Regional) - Sections 11-15")
        print("  - compare: Compare two pages (use compare_pages.py)")
        print("  - accessibility: WCAG and EAA accessibility checks")
        print("  - links: Check for broken links")
        print("  - all: Run all audit types")
        print("\nRegions: US, UK, IE, AU, NZ, MY, SG, IN, HK, PH, PK, TH, VN, ID, FR, DE, IT, ES, NL, BE, AT, CH, NO, DK, SE, JP, KR, CN, TW, CA")
        print("\nExamples:")
        print("  python universal_analyzer_v2.py https://www.dell.com/en-gb --audit-type r2 --region UK")
        print("  python universal_analyzer_v2.py https://www.dell.com/en-us --audit-type accessibility --region US")
        print("  python universal_analyzer_v2.py https://www.dell.com/en-gb --audit-type all --region UK")
        sys.exit(1)
    
    url = sys.argv[1]
    audit_type = "r2"  # Default
    region = "US"  # Default
    
    if "--audit-type" in sys.argv:
        type_index = sys.argv.index("--audit-type")
        if type_index + 1 < len(sys.argv):
            audit_type = sys.argv[type_index + 1].lower()
    
    if "--region" in sys.argv:
        region_index = sys.argv.index("--region")
        if region_index + 1 < len(sys.argv):
            region = sys.argv[region_index + 1].upper()
    
    print("\n" + "="*60)
    print("UNIVERSAL PAGE ANALYZER V2")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  URL: {url}")
    print(f"  Audit Type: {audit_type.upper()}")
    print(f"  Region: {region}")
    print(f"\nStarting analysis...")
    
    analyzer = UniversalAnalyzerV2(url, audit_type, region)
    asyncio.run(analyzer.run())


if __name__ == "__main__":
    main()
