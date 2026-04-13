import { expect, test } from "@playwright/test";

test("renders subject selection screen", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Select exam subject")).toBeVisible();
  await expect(page.getByRole("button", { name: "history" })).toBeVisible();
});
