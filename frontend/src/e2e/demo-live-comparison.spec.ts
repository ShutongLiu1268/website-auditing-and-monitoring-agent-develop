import { test, expect } from "@playwright/test";
import { auditRunResponses, mockAuditApi } from "./mock-audit-api";

const demoPages = [
  {
    url: "https://www.dell.com/en-ca/shop/laptop-computers/spd/dell16laptopdc16251",
    locale: "en-CA",
  },
  {
    url: "https://www.dell.com/en-us/shop/laptop-computers/spd/dell16laptopdc16251",
    locale: "en-US",
  },
  {
    url: "https://www.dell.com/fr-ca/shop/laptop-computers/spd/dell16laptopdc16251",
    locale: "fr-CA",
  },
];

const issue = {
  id: "issue-1",
  run_id: "run-1",
  severity: "critical",
  status: "new",
  rule: "R2 & R3 · Section 2.1",
  category: "Language",
  page: "FR-CA",
  locale: "fr-CA",
  snippet: "Enterprise Upgrades",
  problem: "English fragment remains visible in a French-Canadian PDP zone.",
  correction: "Remplacer par « Mises à niveau professionnelles ».",
  proof: "Exact text found in the configuration selector.",
  locator: "#configuration-selector .upgrade-label",
  evaluator: "DSX · GPT-OSS",
  confidence: 0.94,
  review_required: true,
  capture_url: null,
};

test("cross-page tab shows invariant and market-sensitive facts with run transitions", async ({
  page,
}) => {
  await mockAuditApi(
    page,
    auditRunResponses({
      targets: demoPages,
      issues: [issue],
      comparison: {
        run_id: "run-1",
        previous_run_id: "run-0",
        statuses: {
          resolved: [
            {
              ...issue,
              id: "resolved-1",
              problem: "Old spelling was fixed.",
              status: "resolved",
            },
          ],
        },
        cross_page: [
          {
            field: "memory",
            label: "Memory",
            category: "invariant",
            status: "actionable",
            values: [
              { locale: "en-CA", url: demoPages[0].url, value: "16 GB" },
              { locale: "en-US", url: demoPages[1].url, value: "16 GB" },
              { locale: "fr-CA", url: demoPages[2].url, value: "8 GB" },
            ],
          },
          {
            field: "price",
            label: "Price",
            category: "market_sensitive",
            status: "expected",
            values: [
              { locale: "en-CA", url: demoPages[0].url, value: "CA$1,449.00" },
              { locale: "en-US", url: demoPages[1].url, value: "US$1,299.00" },
              { locale: "fr-CA", url: demoPages[2].url, value: "1 449,00 $ CA" },
            ],
          },
        ],
      },
    }),
  );

  await page.goto("/");
  await page.getByRole("tab", { name: "Cross-page comparison" }).click();

  await expect(page.getByText("Memory", { exact: true })).toBeVisible();
  await expect(page.getByText("Actionable", { exact: true })).toBeVisible();
  await expect(page.getByText("Expected", { exact: true })).toBeVisible();
  await expect(page.getByText("Old spelling was fixed.")).toBeVisible();
});
