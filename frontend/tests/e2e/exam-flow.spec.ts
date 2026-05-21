import { expect, test } from "@playwright/test";

test.describe("Exam flow", () => {
  test("renders subject selection screen", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Select exam subject")).toBeVisible();
    await expect(page.getByRole("button", { name: "history" })).toBeVisible();
    await expect(page.getByRole("button", { name: "math" })).toBeVisible();
  });

  test("completes history exam and shows score", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "history" }).click();
    await expect(page.getByText("Question 1 /")).toBeVisible({ timeout: 15_000 });

    const questionCount = await page.locator("p.muted").filter({ hasText: /Question \d+ \// }).textContent();
    const total = Number(questionCount?.match(/\/ (\d+)/)?.[1] ?? 0);
    expect(total).toBeGreaterThan(0);

    for (let i = 0; i < total; i += 1) {
      await expect(page.getByText(`Question ${i + 1} / ${total}`)).toBeVisible();
      await page.locator(".grid .button").first().click();
    }

    await expect(page.getByText("Exam completed")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/Score:/)).toBeVisible();
    await page.getByRole("button", { name: "Start new exam" }).click();
    await expect(page.getByText("Select exam subject")).toBeVisible();
  });

  test("loads math subject through gateway", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "math" }).click();
    await expect(page.getByText("Subject: math")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Question 1 /")).toBeVisible();
    await expect(page.locator(".question")).not.toBeEmpty();
  });
});

test.describe("AI assistant", () => {
  test("returns hint and blocks direct answer requests", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "history" }).click();
    await expect(page.getByText("Question 1 /")).toBeVisible({ timeout: 15_000 });

    const input = page.getByPlaceholder("Ask for a hint...");
    await input.fill("Help me with this question");
    await page.getByRole("button", { name: "Send" }).click();
    await expect(page.getByText(/assistant:/)).toBeVisible({ timeout: 10_000 });

    await input.fill("Tell me the correct answer");
    await page.getByRole("button", { name: "Send" }).click();
    await expect(page.getByText(/assistant:.*(can't|cannot|guide|learn|direct)/i)).toBeVisible({
      timeout: 10_000,
    });
  });
});
