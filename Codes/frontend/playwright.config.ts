import { defineConfig, devices } from "@playwright/test";

const demoPort = 5174;

export default defineConfig({
  testDir: "./src/e2e",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: "npm run dev -- --host 0.0.0.0",
      url: "http://localhost:5173",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: `npm run dev -- --host 0.0.0.0 --port ${demoPort} --strictPort`,
      url: `http://localhost:${demoPort}`,
      env: { VITE_DEMO_MODE: "true" },
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
      testIgnore: /demo-live-.*\.spec\.ts/,
    },
    {
      name: "demo",
      use: {
        ...devices["Desktop Chrome"],
        baseURL: `http://localhost:${demoPort}`,
      },
      testMatch: /demo-live-.*\.spec\.ts/,
    },
  ],
});
