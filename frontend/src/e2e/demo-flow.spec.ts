import { test, expect } from "@playwright/test";
import { auditRunResponses, mockAuditApi } from "./mock-audit-api";

test.describe("NPL PDP audit demo", () => {
  test("renders audit workspace and DDS workflow controls", async ({
    page,
  }) => {
    await mockAuditApi(page, auditRunResponses());
    await page.goto("/");
    await expect(page.getByText("Run an audit")).toBeVisible();
    await expect(page.getByLabel("What should I inspect?")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Run agent audit" }),
    ).toBeVisible();
    await page
      .getByLabel("What should I inspect?")
      .fill("Audit https://www.dell.com/en-us/shop/laptops");
    await expect(
      page.getByText("https://www.dell.com/en-us/shop/laptops"),
    ).toBeVisible();
    await page.getByRole("button", { name: "Scan options" }).click();
    await expect(page.getByLabel("Review profile")).toBeVisible();
    await page.getByRole("button", { name: "Close dialog" }).click();
    await expect(
      page.getByRole("button", { name: "Open schedules" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Open schedules" }).click();
    await expect(page.getByText("Recurring reports")).toBeVisible();
  });
});
