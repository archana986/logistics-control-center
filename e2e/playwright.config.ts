import { defineConfig } from "@playwright/test";

const appBaseUrl =
  process.env.APP_UI_BASE_URL ||
  process.env.APP_BASE_URL?.replace(/\/api\/?$/, "") ||
  "http://localhost:8000";

export default defineConfig({
  testDir: ".",
  timeout: 120_000,
  retries: 1,
  use: {
    baseURL: appBaseUrl,
    trace: "on-first-retry",
  },
  reporter: [["list"]],
});
