import { test, expect } from "@playwright/test";
import { auditRunResponses, mockAuditApi } from "./mock-audit-api";

test.describe("results stage", () => {
  test("header does not pin the review to three pages", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".results-header h2")).toHaveText("R3 review");
  });

  test("status line counts issues and pages from the prompt run", async ({
    page,
  }) => {
    await mockAuditApi(page, auditRunResponses());
    await page.goto("/");
    await page
      .getByLabel("What should I inspect?")
      .fill("Audit https://www.dell.com/en-us/shop/laptops");
    await page.getByRole("button", { name: "Run agent audit" }).click();

    await expect(page.locator(".run-status > div > span")).toHaveText(
      "0 issues · 1 page in scope · R3",
    );
  });

  test("keeps results labelled with the profile that produced them", async ({
    page,
  }) => {
    await mockAuditApi(page, auditRunResponses());
    await page.goto("/");
    await page
      .getByLabel("What should I inspect?")
      .fill("Audit https://www.dell.com/en-us/shop/laptops");
    await page.getByRole("button", { name: "Run agent audit" }).click();
    await expect(page.getByText("Audit complete")).toBeVisible();

    await page.getByLabel("Review profile").selectOption("sprint_launch");

    await expect(page.locator(".results-header h2")).toHaveText("R3 review");
    await expect(page.locator(".run-status > div > span")).toHaveText(
      "0 issues · 1 page in scope · R3",
    );
  });

  test("rule trace lists failed checkpoints first, then passed, then not applicable", async ({
    page,
  }) => {
    await mockAuditApi(
      page,
      auditRunResponses({
        trace: [
          {
            rule: "SPR-01",
            zone: "hero",
            outcome: "not_applicable",
            evaluator: "code",
          },
          {
            rule: "R2G-05",
            zone: "tech_specs",
            outcome: "pass",
            evaluator: "llm",
          },
          { rule: "D6", zone: "features", outcome: "issue", evaluator: "DSX" },
          { rule: "SPR-12", zone: "page", outcome: "error", evaluator: "DSX" },
          {
            rule: "D9",
            zone: "features",
            outcome: "not_evaluated",
            evaluator: "DSX",
          },
          { rule: "D1", zone: "hero", outcome: "pass", evaluator: "llm" },
        ],
      }),
    );
    await page.goto("/");
    await page
      .getByLabel("What should I inspect?")
      .fill("Audit https://www.dell.com/en-us/shop/laptops");
    await page.getByRole("button", { name: "Run agent audit" }).click();
    await expect(page.getByText("Audit complete")).toBeVisible();

    await page.getByRole("tab", { name: "Rule trace" }).click();

    await expect(page.locator(".trace-row strong")).toHaveText([
      "D6",
      "SPR-12",
      "R2G-05",
      "D1",
      "SPR-01",
      "D9",
    ]);
  });
});
