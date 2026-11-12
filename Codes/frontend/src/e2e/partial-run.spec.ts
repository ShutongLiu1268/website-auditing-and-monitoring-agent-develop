import { test, expect } from "@playwright/test";
import { auditRunResponses, mockAuditApi } from "./mock-audit-api";

test("partial run without demo checkpoints is not reported as complete", async ({
  page,
}) => {
  const responses = auditRunResponses();
  const status = responses["GET /api/runs/run-1/status"] as Record<
    string,
    unknown
  >;
  await mockAuditApi(page, {
    ...responses,
    "GET /api/runs/run-1/status": {
      ...status,
      status: "partial",
      warnings: ["fixture_checkpoints_unavailable:sprint_launch"],
    },
  });
  await page.goto("/");
  await page.getByLabel("Review profile").selectOption("sprint_launch");
  await page
    .getByLabel("What should I inspect?")
    .fill("Audit https://www.dell.com/en-us/shop/laptops");
  await page.getByRole("button", { name: "Run agent audit" }).click();

  await expect(page.getByText("Audit complete")).toHaveCount(0);
  await expect(page.locator(".run-status strong")).toHaveText("Partial audit");
  await expect(
    page.getByText(
      "No demo checkpoints for Sprint/Launch, so findings were not evaluated.",
    ),
  ).toBeVisible();
});
