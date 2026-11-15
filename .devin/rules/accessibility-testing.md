---
trigger: always_on
---

# Accessibility testing

When the user requests accessibility testing on a page:

- Run WCAG 2.1/2.2 and European Accessibility Act (EAA) compliance checks
- Check at minimum: color contrast (4.5:1 for normal text), heading structure (single H1, logical order), alt text on images, form labels, keyboard navigability, and focus indicators
- Report each violation with severity, the element or section affected, and a concrete fix
- Present results in the standard findings table (Original Problem, Severity, Issue, Suggested Fix)
