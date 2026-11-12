import type { Page } from "@playwright/test";

export type MockActivity = {
  stage: string;
  message: string;
  page: string | null;
  at: string;
};

type PromptPage = { url: string; locale: string };

export async function mockAuditApi(
  page: Page,
  responses: Record<string, unknown>,
) {
  await page.addInitScript((mocks: Record<string, unknown>) => {
    const apiOrigin = "http://localhost:8000";
    const requested: string[] = [];
    Object.defineProperty(window, "auditApiRequests", { value: requested });

    const realFetch = window.fetch.bind(window);
    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = new URL(String(input), apiOrigin);
      if (url.origin !== apiOrigin) return realFetch(input, init);
      const key = `${init?.method ?? "GET"} ${url.pathname}`;
      requested.push(key);
      const body = mocks[key];
      return new Response(
        JSON.stringify(body === undefined ? { detail: "Not Found" } : body),
        {
          status: body === undefined ? 404 : 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    };

    class MockEventSource {
      readyState = 0;
      private listeners = new Map<
        string,
        Array<(event: { data: string }) => void>
      >();

      constructor(url: string) {
        const path = new URL(url).pathname;
        requested.push(`SSE ${path}`);
        const events = (mocks[`SSE ${path}`] as unknown[] | undefined) ?? [];
        window.setTimeout(() => {
          events.forEach((event) => this.emit("activity", event));
          this.emit("done", {});
          this.readyState = 2;
        }, 0);
      }

      addEventListener(
        type: string,
        listener: (event: { data: string }) => void,
      ) {
        this.listeners.set(type, [
          ...(this.listeners.get(type) ?? []),
          listener,
        ]);
      }

      close() {
        this.readyState = 2;
      }

      private emit(type: string, payload: unknown) {
        (this.listeners.get(type) ?? []).forEach((listener) =>
          listener({ data: JSON.stringify(payload) }),
        );
      }
    }
    window.EventSource = MockEventSource as unknown as typeof EventSource;
  }, responses);
}

export function auditApiRequests(page: Page) {
  return page.evaluate(
    () =>
      (window as unknown as { auditApiRequests: string[] }).auditApiRequests,
  );
}

export function auditRunResponses({
  targets = [
    { url: "https://www.dell.com/en-us/shop/laptops", locale: "en-US" },
  ],
  parse,
  issues = [],
  comparison = {
    run_id: "run-1",
    previous_run_id: null,
    statuses: {},
    cross_page: [],
  },
  trace = [],
  activity = [],
}: {
  targets?: PromptPage[];
  parse?: { targets: PromptPage[]; problems: string[] };
  issues?: unknown[];
  comparison?: unknown;
  trace?: unknown[];
  activity?: MockActivity[];
} = {}): Record<string, unknown> {
  return {
    "POST /api/prompt/parse": parse ?? { targets, problems: [] },
    "POST /api/prompt/runs": {
      audit_id: "audit-1",
      run_id: "run-1",
      mode: "r3",
      targets,
    },
    "GET /api/runs/run-1/status": {
      run_id: "run-1",
      audit_definition_id: "audit-1",
      status: "completed",
      progress: 100,
      total_pages: targets.length,
      completed_pages: targets.length,
      failed_pages: 0,
      warnings: [],
      coverage: {
        scanned: targets.length,
        skipped: 0,
        duplicate: 0,
        inaccessible: 0,
        timeout: 0,
      },
      pages: [],
    },
    "GET /api/runs/run-1/issues": issues,
    "GET /api/runs/run-1/comparison": comparison,
    "GET /api/runs/run-1/trace": trace,
    "SSE /api/runs/run-1/events": activity,
  };
}
