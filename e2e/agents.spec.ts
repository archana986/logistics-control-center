import { expect, test } from "@playwright/test";

function apiBase(baseURL: string | undefined): string {
  if (!baseURL) return "http://localhost:8001/api";
  return `${baseURL.replace(/\/$/, "")}/api`;
}

test("api health endpoint reports backend state", async ({ request, baseURL }) => {
  const response = await request.get(`${apiBase(baseURL)}/health`);
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.status).toBe("ok");
  expect(payload).toHaveProperty("databricks_connected");
  expect(payload).toHaveProperty("database_connected");
});

test("knowledge and customer update endpoints respond", async ({ request, baseURL }) => {
  const health = await request.get(`${apiBase(baseURL)}/health`);
  expect(health.ok()).toBeTruthy();
  const healthPayload = await health.json();

  const update = await request.post(`${apiBase(baseURL)}/generate-customer-update`, {
    data: {
      customerName: "techcorp",
      laneId: "BNA-STL-AIR",
      strategy: {
        strategy: "AIR-VIA-ATL",
        deltaETAminutes: -20,
        addedCostUSD: 200,
        capacityUsedPct: 50,
        notes: "playwright test",
      },
      incidentSummary: "Integration test incident summary",
    },
  });
  expect(update.ok()).toBeTruthy();
  const updatePayload = await update.json();
  expect(updatePayload.message).toBeTruthy();
  expect(["databricks", "fallback"]).toContain(updatePayload.source);

  const kaConfigured = !!(healthPayload.ka_env_var || healthPayload.agents_ka_endpoint);
  test.skip(!kaConfigured, "Knowledge Assistant endpoint is not configured.");

  const knowledge = await request.post(`${apiBase(baseURL)}/knowledge/query`, {
    data: {
      question: "Summarize best practices for weather incident response.",
    },
  });
  expect(knowledge.ok()).toBeTruthy();
  const knowledgePayload = await knowledge.json();
  if (knowledgePayload.source === "error") {
    test.skip(true, `Knowledge Assistant returned error: ${knowledgePayload.answer}`);
  }
  expect(knowledgePayload.answer).toBeTruthy();
});
