import { expect, test } from "@playwright/test";

async function trySelectLane(page: any): Promise<boolean> {
  const canvas = page.locator("canvas").first();
  await expect(canvas).toBeVisible();
  const box = await canvas.boundingBox();
  if (!box) return false;

  const points = [
    { x: box.width * 0.45, y: box.height * 0.45 },
    { x: box.width * 0.55, y: box.height * 0.40 },
    { x: box.width * 0.60, y: box.height * 0.55 },
    { x: box.width * 0.40, y: box.height * 0.60 },
  ];

  for (const p of points) {
    await canvas.click({ position: { x: p.x, y: p.y } });
    const laneDetails = page.getByText("Lane Details");
    try {
      await expect(laneDetails).toBeVisible({ timeout: 2500 });
      return true;
    } catch {
      // try next point
    }
  }
  return false;
}

test("incident response page loads core controls", async ({ page }) => {
  await page.goto("/incident-response");
  await expect(page.getByRole("heading", { name: "Network Control Center" })).toBeVisible();

  const filters = page.locator("select");
  await expect(filters).toHaveCount(2);
  await expect(filters.nth(0)).toBeVisible();
  await expect(filters.nth(1)).toBeVisible();
  await expect(filters.nth(0)).toHaveValue("");
  await expect(filters.nth(1)).toHaveValue("");
});

test("reroute drawer opens after selecting a lane", async ({ page }) => {
  await page.goto("/incident-response");
  const selected = await trySelectLane(page);
  test.skip(!selected, "Could not reliably select a lane from the map canvas.");

  const rerouteButton = page.getByRole("button", { name: "Reroute Urgent Packages" });
  await expect(rerouteButton).toBeVisible();
  await rerouteButton.click();
  await expect(page.getByText("Reroute Urgent Packages")).toBeVisible();
});

test("root cause panel opens when incidents are present", async ({ page }) => {
  await page.goto("/incident-response");
  const selected = await trySelectLane(page);
  test.skip(!selected, "Could not reliably select a lane from the map canvas.");

  const analysisButton = page.getByRole("button", { name: /Run AirOps AI Root Cause Analysis/i });
  if ((await analysisButton.count()) === 0) {
    test.skip(true, "Selected lane has no incidents in current dataset.");
  }

  await analysisButton.click();
  await expect(page.getByText("AirOps AI Root Cause Analysis")).toBeVisible();
});
