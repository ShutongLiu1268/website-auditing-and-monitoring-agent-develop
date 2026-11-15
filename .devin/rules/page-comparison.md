---
description: "Page comparison audit - apply when the user asks to compare two pages/URLs"
trigger: model_decision
---

# Page comparison

When the user requests a page comparison:

- Always ask for BOTH URLs before running (primary page and comparison page)
- For EACH page, capture BOTH the rendered screenshot AND the full page text before comparing
- Compare side by side: content, specs, pricing, checkpoint compliance, spelling/region issues, and accessibility
- Distinguish expected regional differences (currency, units, legal requirements, localized terminology) from actual issues
- Present a side-by-side summary table of key differences first
- Then present findings in the standard findings table format (Original Problem, Severity, Issue, Suggested Fix, Original Link) with a Suggested Fix column describing the recommended change for each difference/issue found
