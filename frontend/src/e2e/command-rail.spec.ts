import { test, expect } from "@playwright/test";
import { auditRunResponses, mockAuditApi } from "./mock-audit-api";

test.describe("command rail", () => {
  test("loads the DDS icon font used by icon actions", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".topbar .dds__icon").first()).toBeVisible();
    const loadedFaces = await page.evaluate(async () =>
      (await document.fonts.load('16px "dds-icons"')).map(
        (face) => face.status,
      ),
    );
    expect(loadedFaces).toEqual(["loaded"]);
  });

  test("reads PDP URLs and locales from the prompt", async ({ page }) => {
    await mockAuditApi(
      page,
      auditRunResponses({
        targets: [
          { url: "https://www.dell.com/en-ca/shop/laptops", locale: "en-CA" },
        ],
      }),
    );
    await page.goto("/");
    await expect(
      page.getByRole("button", { name: "Run agent audit" }),
    ).toBeDisabled();

    await page
      .getByLabel("What should I inspect?")
      .fill("Audit https://www.dell.com/en-ca/shop/laptops");

    await expect(
      page.getByRole("button", { name: "Run agent audit" }),
    ).toBeEnabled();
    await expect(page.getByText("en-CA").first()).toBeVisible();
  });

  test("keeps the audit disabled when a prompt URL has no locale", async ({
    page,
  }) => {
    const problem =
      "No locale found for https://www.dell.com/shop/laptops. Add it to the URL path or after the URL, e.g. en-CA.";
    await mockAuditApi(
      page,
      auditRunResponses({ parse: { targets: [], problems: [problem] } }),
    );
    await page.goto("/");

    await page
      .getByLabel("What should I inspect?")
      .fill("Audit https://www.dell.com/shop/laptops");

    await expect(page.getByText(problem)).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Run agent audit" }),
    ).toBeDisabled();
  });
});
