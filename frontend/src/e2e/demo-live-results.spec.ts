import { test, expect } from "@playwright/test";
import {
  auditApiRequests,
  auditRunResponses,
  mockAuditApi,
} from "./mock-audit-api";

const issue = {
  id: "live-issue-1",
  run_id: "run-1",
  severity: "high",
  status: "new",
  rule: "R3 · Section 2.1",
  category: "Language",
  page: "EN-CA",
  locale: "en-CA",
  snippet: "Live snippet",
  problem: "Live API problem text",
  correction: "Live correction",
  proof: "Live proof text",
  locator: "#live-locator",
  evaluator: "DSX · GPT-OSS",
  confidence: 0.94,
  review_required: true,
  capture_url: null,
  reasoning: "Live reasoning text",
};

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

test.describe("demo live results", () => {
  test("renders findings, comparison, rule trace, and bot activity from the live API", async ({
    page,
  }) => {
    await mockAuditApi(
      page,
      auditRunResponses({
        targets: demoPages,
        issues: [issue],
        comparison: {
          run_id: "run-1",
          previous_run_id: null,
          statuses: {
            new: [
              {
                ...issue,
                id: "live-compare-1",
                problem: "Live comparison problem",
              },
            ],
          },
        },
        trace: [
          {
            rule: "R3 · Section 2.1",
            zone: "configuration_selector",
            outcome: "issue",
            evaluator: "DSX",
            detail: "Live trace detail",
            reasoning: "Live trace reasoning",
          },
        ],
        activity: [
          {
            stage: "render",
            message: "Rendering en-CA page",
            page: "en-CA",
            at: "2026-10-09T09:42:00Z",
          },
        ],
      }),
    );

    await page.goto("/");

    await expect(page.getByText("Live API problem text").first()).toBeVisible();
    await expect(page.getByText("Live reasoning text").first()).toBeVisible();
    await expect(
      page.getByText("English fragment remains visible"),
    ).toHaveCount(0);
    await expect(page.getByText("Rendering en-CA page")).toBeVisible();

    await page.getByRole("tab", { name: "Cross-page comparison" }).click();
    await expect(page.getByText("Live comparison problem")).toBeVisible();

    await page.getByRole("tab", { name: "Rule trace" }).click();
    await expect(page.getByText("Live trace detail")).toBeVisible();
    await expect(page.getByText("Live trace reasoning")).toBeVisible();

    expect(await auditApiRequests(page)).toEqual(
      expect.arrayContaining([
        "POST /api/prompt/runs",
        "SSE /api/runs/run-1/events",
      ]),
    );
  });
});
