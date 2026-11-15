---
trigger: always_on
---

# Ask which audit type and checkpoint before running

Whenever the user asks to audit a URL, always ask BOTH questions BEFORE running anything:

1. What kind of checkpoint do they want? Options: Sprint/Launch, R2, R3 (or specify another framework)
2. Which check do they want? Options:
   - R2 Review (Sections 1-10: spelling, dimensions, superlatives, footnotes, trademarks, etc.)
   - R3 Review (Sections 11-15: regional content)
   - Comparison (requires a second URL)
   - Accessibility (WCAG/EAA compliance)
   - Broken links check
   - All checks

Do not run any audit until the user has told you which checkpoint and which check(s) they want.
