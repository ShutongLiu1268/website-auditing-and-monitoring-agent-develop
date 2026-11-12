import { test, expect } from "@playwright/test";
import { auditRunResponses, mockAuditApi } from "./mock-audit-api";

test.describe("prompt route", () => {
  test("asks for a backend restart when the prompt route is missing", async ({
    page,
  }) => {
    await mockAuditApi(page, {});
    await page.goto("/");

    await page
      .getByLabel("What should I inspect?")
      .fill("Audit https://www.dell.com/en-ca/shop/laptops");

    await expect(
      page.getByText("Restart the backend to load the latest routes."),
    ).toBeVisible();
  });

  test("lists every PDP URL the prompt contains", async ({ page }) => {
    const pages = [
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
    await mockAuditApi(page, auditRunResponses({ targets: pages }));
    await page.goto("/");

    await page
      .getByLabel("What should I inspect?")
      .fill(
        "Can you help me to audit those 3 pages against R3 checkpoints: 1. https://www.dell.com/en-ca/shop/laptop-computers/spd/dell16laptopdc16251  2.https://www.dell.com/en-us/shop/laptop-computers/spd/dell16laptopdc16251 3. https://www.dell.com/fr-ca/shop/laptop-computers/spd/dell16laptopdc16251",
      );

    await expect(page.locator(".target-section .section-count")).toHaveText(
      "03",
    );
    await expect(page.locator(".target-row-readonly strong")).toHaveText([
      "en-CA",
      "en-US",
      "fr-CA",
    ]);
  });
});
