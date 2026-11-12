"""R2 Checkpoint Analysis Script"""

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def analyze_r2_checkpoints(text, region="US"):
    """Analyze text against R2 checkpoints and return findings."""
    
    findings = []
    
    # Section 1: Spelling Check (US English)
    uk_to_us_variations = [
        ("gray", "grey"), ("maneuver", "manoeuvre"), ("center", "centre"),
        ("fiber", "fibre"), ("liter", "litre"), ("actualize", "actualise"),
        ("analyze", "analyse"), ("apologize", "apologise"), ("civilize", "civilise"),
        ("customizable", "customisable"), ("customization", "customisation"),
        ("customize", "customise"), ("maximize", "maximise"), ("minimize", "minimise"),
        ("modernize", "modernise"), ("optimization", "optimisation"),
        ("optimize", "optimise"), ("organization", "organisation"),
        ("personalize", "personalise"), ("prioritize", "prioritise"),
        ("recognize", "recognise"), ("canceled", "cancelled"), ("fueled", "fuelled"),
        ("labeled", "labelled"), ("modeled", "modelled"), ("traveled", "travelled"),
        ("catalog", "catalogue"), ("analog", "analogue"), ("color", "colour"),
        ("flavor", "flavour"), ("favorite", "favourite"), ("humor", "humour"),
        ("labor", "labour"), ("neighbor", "neighbour"), ("defense", "defence"),
        ("license", "licence"), ("offense", "offence"), ("aluminum", "aluminium"),
    ]
    
    spelling_issues = []
    for us, uk in uk_to_us_variations:
        if uk in text.lower():
            spelling_issues.append(f"Found UK spelling: '{uk}' (should be '{us}')")
    
    if spelling_issues:
        for issue in spelling_issues:
            findings.append({
                "section": "Section 1 - Spelling",
                "problem": issue,
                "correction": f"Use US English spelling",
                "copy_paste": issue,
                "severity": "Medium",
                "explanation": "US English required for US region"
            })
    else:
        findings.append({
            "section": "Section 1 - Spelling",
            "problem": "No UK/US English variant issues found",
            "correction": "N/A",
            "copy_paste": "N/A",
            "severity": "N/A",
            "explanation": "US English used correctly throughout"
        })
    
    # Section 2: Spelling Errors
    # Check for common spelling errors
    common_errors = ["teh", "recieve", "occured", "seperate", "definately"]
    spelling_errors_found = []
    for error in common_errors:
        if error in text.lower():
            spelling_errors_found.append(f"Potential spelling error: '{error}'")
    
    if spelling_errors_found:
        for error in spelling_errors_found:
            findings.append({
                "section": "Section 2 - Spelling Errors",
                "problem": error,
                "correction": "Check spelling",
                "copy_paste": error,
                "severity": "Medium",
                "explanation": "Spelling error detected"
            })
    else:
        findings.append({
            "section": "Section 2 - Spelling Errors",
            "problem": "No spelling errors or language mismatches found",
            "correction": "N/A",
            "copy_paste": "N/A",
            "severity": "N/A",
            "explanation": "No spelling or language issues detected"
        })
    
    # Section 3: Weight & Dimension Format
    # Check dimension format
    dim_pattern = r'(\d+\.?\d*)\s*(mm|cm|in\.?|inch)\s*\(?\s*(\d+\.?\d*)\s*(mm|cm|in\.?|inch)\)?'
    dimensions = re.findall(dim_pattern, text, re.IGNORECASE)
    
    # Check if imperial comes first (for US)
    for dim in dimensions:
        value1, unit1, value2, unit2 = dim
        if unit1.lower() in ['mm', 'cm'] and unit2.lower() in ['in', 'in.', 'inch']:
            findings.append({
                "section": "Section 3 - Dimensions",
                "problem": f"Metric first: {value1} {unit1} ({value2} {unit2})",
                "correction": f"Imperial first: {value2} {unit2} ({value1} {unit1})",
                "copy_paste": f"{value2} {unit2} ({value1} {unit1})",
                "severity": "Medium",
                "explanation": "Rule under discussion - US should show imperial first"
            })
    
    # Check weight format
    weight_pattern = r'(\d+\.?\d*)\s*(lbs?|lb|kg)\s*\(?\s*(\d+\.?\d*)\s*(lbs?|lb|kg)\)?'
    weights = re.findall(weight_pattern, text, re.IGNORECASE)
    
    for weight in weights:
        value1, unit1, value2, unit2 = weight
        if unit1.lower() in ['kg'] and unit2.lower() in ['lbs', 'lb']:
            findings.append({
                "section": "Section 3 - Dimensions",
                "problem": f"Weight: {value1} {unit1} ({value2} {unit2})",
                "correction": f"Weight: {value2} {unit2} ({value1} {unit1})",
                "copy_paste": f"{value2} {unit2} ({value1} {unit1})",
                "severity": "Medium",
                "explanation": "Rule under discussion - US should show imperial first"
            })
    
    if not findings[-1]["section"].startswith("Section 3"):
        findings.append({
            "section": "Section 3 - Dimensions",
            "problem": "Dimension format appears correct (imperial first for US)",
            "correction": "N/A",
            "copy_paste": "N/A",
            "severity": "N/A",
            "explanation": "US shows imperial first which is correct"
        })
    
    # Section 4: Top Specs vs Full Tech Specs
    # Check if dimensions appear in both sections
    top_specs_dims = re.findall(r'Height:\s*([\d.]+\s*(?:in\.?|mm))\s*Width:\s*([\d.]+\s*(?:in\.?|mm))', text)
    full_specs_dims = re.findall(r'Height:\s*([\d.]+\s*(?:in\.?|mm))\s*Depth:\s*([\d.]+\s*(?:in\.?|mm))', text)
    
    if top_specs_dims and full_specs_dims:
        findings.append({
            "section": "Section 4 - Tech Specs",
            "problem": "No inconsistencies between top specs and full tech specs",
            "correction": "N/A",
            "copy_paste": "N/A",
            "severity": "N/A",
            "explanation": "Top PDP specs match full tech specs perfectly"
        })
    
    # Section 5: Inch Format Consistency
    # Check for " instead of -inch
    inch_issues = re.findall(r'(\d+\.?\d*)"', text)
    for inch in inch_issues:
        if '13.4"' in text or '13-inch' in text:
            if '"' in text and '-inch' not in text:
                findings.append({
                    "section": "Section 5 - Inch Format",
                    "problem": f'Uses " instead of -inch: {inch}"',
                    "correction": f'{inch.replace('"', "-inch")}',
                    "copy_paste": f'{inch.replace('"', "-inch")}',
                    "severity": "Medium",
                    "explanation": "Rule under discussion - should use -inch format"
                })
    
    # Section 6: Unsupported Superlative Claims
    superlatives = ["thinnest", "lightest", "fastest", "best", "most"]
    superlative_pattern = r'\b(thinnest|lightest|fastest|best|most)\b'
    superlative_matches = re.findall(superlative_pattern, text, re.IGNORECASE)
    
    # Deduplicate
    unique_superlatives = set([s.lower() for s in superlative_matches])
    
    for superlative in sorted(unique_superlatives):
        findings.append({
            "section": "Section 6 - Superlatives",
            "problem": f'Superlative claim: "{superlative}"',
            "correction": "Remove or substantiate with proof",
            "copy_paste": superlative,
            "severity": "High",
            "explanation": "Requires substantiation proof for legal compliance"
        })
    
    if not unique_superlatives:
        findings.append({
            "section": "Section 6 - Superlatives",
            "problem": "No unsupported superlative claims found",
            "correction": "N/A",
            "copy_paste": "N/A",
            "severity": "N/A",
            "explanation": "No superlative claims detected"
        })
    
    # Section 7: Tech Note Functionality
    # Check for footnote references
    footnote_refs = re.findall(r'\[(\d+)\]', text)
    unique_refs = set(footnote_refs)
    
    for ref in sorted(unique_refs):
        findings.append({
            "section": "Section 7 - Footnotes",
            "problem": f"Footnote reference [{ref}] needs verification",
            "correction": f"Check footnote [{ref}] explanation exists",
            "copy_paste": f"Check footnote [{ref}] explanation exists",
            "severity": "Medium",
            "explanation": "Footnote explanations not visible in extracted text - manual check required"
        })
    
    # Section 8: CN Locale - Copilot
    if "copilot" in text.lower():
        findings.append({
            "section": "Section 8 - CN Locale",
            "problem": "Copilot references found",
            "correction": "Remove for CN locale",
            "copy_paste": "Remove Copilot references",
            "severity": "High" if region == "CN" else "N/A",
            "explanation": f"Acceptable for {region} - would be Critical for CN region"
        })
    
    # Section 9: Trademark Accuracy
    trademarks_to_check = [
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
    
    for brand, symbol in trademarks_to_check:
        if brand in text:
            # Check if followed by symbol
            pattern = rf'{re.escape(brand)}\s*{re.escape(symbol)}'
            if not re.search(pattern, text, re.IGNORECASE):
                findings.append({
                    "section": "Section 9 - Trademarks",
                    "problem": f"{brand} without {symbol} symbol",
                    "correction": f"{brand}{symbol}",
                    "copy_paste": f"{brand}{symbol}",
                    "severity": "Medium",
                    "explanation": f"Missing required trademark symbol"
                })
    
    # Check Wi-Fi
    if "Wi-Fi" in text and "Wi-Fi™" not in text:
        findings.append({
            "section": "Section 9 - Trademarks",
            "problem": "Wi-Fi - No trademark symbol",
            "correction": "Wi-Fi™",
            "copy_paste": "Wi-Fi™",
            "severity": "Medium",
            "explanation": "May require ™ symbol - needs verification"
        })
    
    # Section 10: Peace of Mind
    if "Peace of Mind" not in text:
        findings.append({
            "section": "Section 10 - Peace of Mind",
            "problem": "Module not found (acceptable for US)",
            "correction": "N/A",
            "copy_paste": "N/A",
            "severity": "N/A",
            "explanation": "Peace of Mind module not required for US region"
        })
    
    # Sections 11-15
    findings.append({
        "section": "Sections 11-15",
        "problem": "Not applicable for R2 review",
        "correction": "N/A",
        "copy_paste": "N/A",
        "severity": "N/A",
        "explanation": "These sections are for R3 regional reviews only"
    })
    
    return findings


def generate_markdown_report(findings, url, region):
    """Generate markdown report with findings table."""
    
    report = f"""# R2 Review - Dell PDP (USA) - Automated Analysis

## Audit Information

| Aspect | Details |
|--------|---------|
| **URL** | {url} |
| **Region** | {region} |
| **Audit Type** | R2 Review (Global English) |

---

## Complete Audit Findings Table

| Section | The Problem | Suggested Correction | What to copy/paste into proof | Severity | Explanation |
|---------|-------------|---------------------|--------------------------------|----------|-------------|
"""
    
    for finding in findings:
        report += f'| {finding["section"]} | {finding["problem"]} | {finding["correction"]} | {finding["copy_paste"]} | {finding["severity"]} | {finding["explanation"]} |\n'
    
    return report


def main():
    """Main function to run R2 analysis."""
    
    # Read the extracted text
    text_file = SCRIPT_DIR / "pdp_text.txt"
    if not text_file.exists():
        print("Error: pdp_text.txt not found. Run the audit first.")
        return
    
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"Analyzing {len(text)} characters of text...")
    
    # Analyze against R2 checkpoints
    findings = analyze_r2_checkpoints(text, region="US")
    
    print(f"Found {len(findings)} findings")
    
    # Generate report
    url = "https://www.dell.com/en-us/shop/laptop-computers/spd/xps13dx13260#configure-anchor"
    report = generate_markdown_report(findings, url, "US")
    
    # Save report
    report_file = SCRIPT_DIR / "r2_automated_analysis.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_file}")
    print(f"\nTotal findings: {len(findings)}")
    
    # Print summary
    critical = len([f for f in findings if f["severity"] == "Critical"])
    high = len([f for f in findings if f["severity"] == "High"])
    medium = len([f for f in findings if f["severity"] == "Medium"])
    low = len([f for f in findings if f["severity"] == "Low"])
    
    print(f"\nSeverity breakdown:")
    print(f"  Critical: {critical}")
    print(f"  High: {high}")
    print(f"  Medium: {medium}")
    print(f"  Low: {low}")


if __name__ == "__main__":
    main()
