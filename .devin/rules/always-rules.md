---
trigger: always_on
---

# Always-On Rules for Website Auditing and Monitoring Agent

## Confirm the task before starting

No matter what the user asks, always state what task you are about to do before starting work. Briefly restate your understanding of the request and confirm it with the user before making any changes.

## Ask which audit type and checkpoint before running

Whenever the user asks to audit a URL, ask ONE question BEFORE running anything:

"Which checkpoint/framework should I apply to this page?"

Options:
1. Sprint/Launch
2. R2 Review (Sections 1-10: spelling, dimensions, superlatives, footnotes, trademarks, etc.)
3. R3 Review (Sections 11-15: regional content)
4. Accessibility testing (WCAG 2.1/2.2 and EAA compliance)
5. Page comparison (requires a second URL)

If the user picks Page comparison, also ask for the second URL before running.

Do not run any audit until the user has told you which checkpoint/framework they want.

## Audit Process Requirements

When performing any URL audit (Sprint/Launch, R2, R3, Accessibility, or Page Comparison), always follow this process:

1. **Open the URL** - Use browser_preview to open the target URL in a browser session (if available)
2. **Take screenshots** - Capture visual screenshots of the page to review visual elements, layout, and imagery
   - **Preferred method: Use Playwright via simple_screenshot.py**
     - Install Playwright if not available: `python -m pip install playwright`
     - Install Chromium browser: `python -m playwright install chromium`
     - Run screenshot: `cd backend && python simple_screenshot.py "<URL>" <output_filename>.png`
     - Example: `python simple_screenshot.py "https://www.dell.com/en-ca/shop/laptop-computers/spd/dell15laptopdc15250" dell15laptop_ca.png`
   - **Alternative method: Use screenshot.py for multiple URLs**
     - Edit the URLS list in `backend/screenshot.py` to add your target URLs
     - Run: `cd backend && python screenshot.py`
   - **Fallback: If Playwright is not available**, use browser_preview to capture the page visually
3. **Read content from screenshots** - Analyze the visual content from screenshots for issues like:
   - Missing imagery
   - Broken videos or animations
   - Visual formatting issues
   - Accessibility issues (color contrast, focus indicators, etc.)
4. **Read page content** - Use webfetch to retrieve the text/HTML content of the page for:
   - Spelling and grammar checks
   - Trademark verification
   - Footnote reference checks
   - Dimension and weight format validation
   - Link validation
   - Text-based content analysis

**Important:** Both visual (screenshot) and text-based analysis must be performed for a complete audit. Do not rely solely on webfetch text content.

**Screenshot Method Details:**
- The `simple_screenshot.py` script uses Playwright to launch a headless Chromium browser
- It navigates to the URL, waits for page rendering, dismisses cookie banners
- It scrolls through the page to trigger lazy loading of all content
- It takes a full-page screenshot and saves it to the backend directory
- The script handles common cookie banner selectors automatically
- Use the screenshot file path to read the image with the `read` tool for visual analysis

**Sprint/Launch Audit Checkpoints:** If the user selects Sprint/Launch audit, always check the following:
- Accuracy, consistency, and compliance with Dell style and language rules
- R2 and R3 requirements
- Compare tech specs and PDP for inconsistencies
- Call out any accessibility issues that would be flagged by WCAG or the EAA

## Thorough Screenshot Analysis Requirement

When analyzing screenshots for any audit, ALWAYS perform a comprehensive visual analysis including:

1. **Error messages and warnings** - Look for any visible error messages, "Sold Out" badges, or disabled buttons
2. **Image and media issues** - Check for broken images, missing imagery, repetitive alt text labels visible on screen, broken videos or animations
3. **Visual formatting issues** - Look for text formatting problems (e.g., strikethrough using combining characters instead of CSS), layout issues, spacing problems
4. **UI element states** - Check button states (enabled/disabled), form field states, interactive element appearance
5. **Accessibility visual indicators** - Check for color contrast issues, missing focus indicators, lack of visual hierarchy
6. **Content inconsistencies** - Compare visual elements with text content for discrepancies (e.g., pricing, product names, specifications)
7. **Typography and spelling** - Look for visible spelling errors, inconsistent capitalization, British vs. American/Canadian spelling inconsistencies

**Important:** Screenshot analysis must be as thorough as text content analysis. Do not rely solely on webfetch text content. All visual issues found in screenshots must be reported in the audit findings table with "Screenshot" as the source.

## Audit findings table format

Whenever presenting audit results or findings in a table, always include these columns:

1. **Original Problem** - the exact text or issue found on the page
2. **Severity** - Critical / High / Medium / Low
3. **Issue** - which checkpoint or section was violated
4. **Suggested Fix** - how to fix it
5. **Source** - where the issue was found (Screenshot or Webfetch, with specific section/area noted)
6. **Original Link** - the exact URL where the issue was found (for broken links, the broken URL; for page content issues, the page URL)

## Accessibility testing

When the user requests accessibility testing on a page:

- Run WCAG 2.1/2.2 and European Accessibility Act (EAA) compliance checks
- Check at minimum: color contrast (4.5:1 for normal text), heading structure (single H1, logical order), alt text on images, form labels, keyboard navigability, and focus indicators
- Report each violation with severity, the element or section affected, and a concrete fix
- Present results in the standard findings table (Original Problem, Severity, Issue, Suggested Fix, Source, Original Link)

## Git and GitHub Operations

When the user asks to connect a project to GitHub or push changes:

### Installing Git (if not already installed)
1. Check if Git is installed: `git --version` or `where git`
2. If not installed, download the Git installer:
   - Download from https://github.com/git-for-windows/git/releases/download/v2.47.0.windows.2/Git-2.47.0.2-64-bit.exe
   - Or use winget: `winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements`
3. Run the installer silently to user directory (to avoid permission issues):
   ```powershell
   Invoke-WebRequest -Uri "https://github.com/git-for-windows/git/releases/download/v2.47.0.windows.2/Git-2.47.0.2-64-bit.exe" -OutFile "$env:TEMP\Git-installer.exe"
   Start-Process -FilePath "$env:TEMP\Git-installer.exe" -ArgumentList "/VERYSILENT", "/NORESTART", "/DIR=$env:LOCALAPPDATA\Git" -Wait
   ```
4. Verify installation: `& "$env:LOCALAPPDATA\Git\bin\git.exe" --version`

### Connecting to GitHub
1. Initialize git repository in the project directory:
   ```powershell
   & "$env:LOCALAPPDATA\Git\bin\git.exe" -C "C:\path\to\project" init
   ```
2. Check if remote already exists:
   ```powershell
   & "$env:LOCALAPPDATA\Git\bin\git.exe" -C "C:\path\to\project" remote -v
   ```
3. If no remote exists, add it:
   ```powershell
   & "$env:LOCALAPPDATA\Git\bin\git.exe" -C "C:\path\to\project" remote add origin https://github.com/USERNAME/REPO.git
   ```

### Committing and Pushing Changes
1. Add all changes:
   ```powershell
   & "$env:LOCALAPPDATA\Git\bin\git.exe" -C "C:\path\to\project" add .
   ```
2. Check status to see what will be committed:
   ```powershell
   & "$env:LOCALAPPDATA\Git\bin\git.exe" -C "C:\path\to\project" status
   ```
3. Commit with a descriptive message:
   ```powershell
   & "$env:LOCALAPPDATA\Git\bin\git.exe" -C "C:\path\to\project" commit -m "Your commit message here"
   ```
4. Push to GitHub:
   ```powershell
   & "$env:LOCALAPPDATA\Git\bin\git.exe" -C "C:\path\to\project" push
   ```

**Note:** Use the full path to git.exe (`$env:LOCALAPPDATA\Git\bin\git.exe`) to ensure it works even if git is not in the system PATH. Use the `-C` flag to specify the repository directory.
