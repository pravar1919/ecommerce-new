import { expect, test } from "@playwright/test";

import { HOME_SECTIONS, sectionOrder } from "./helpers";

test.describe("homepage", () => {
  test("renders all 14 sections in order, server-side", async ({ page, request }) => {
    const html = await (await request.get("/")).text();
    for (const s of new Set(HOME_SECTIONS))
      expect(html, `SSR html contains ${s}`).toContain(`data-section="${s}"`);

    await page.goto("/");
    await expect(page.locator("[data-section=hero]")).toBeVisible();
    await expect.poll(() => sectionOrder(page)).toEqual(HOME_SECTIONS);
  });

  test("has one h1, landmarks, alt text and the dev identity pill", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.getByRole("banner")).toBeVisible();
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByRole("contentinfo")).toBeAttached();
    const missingAlt = await page.locator("img:not([alt])").count();
    expect(missingAlt).toBe(0);
    await expect(page.getByRole("link", { name: /home/ }).first()).toContainText("DEV");
  });

  test("hero image is the prioritised LCP candidate and served same-origin", async ({ page }) => {
    await page.goto("/");
    const hero = page.locator("[data-section=hero] img").first();
    await expect(hero).toHaveAttribute("fetchpriority", "high");
    const src = (await hero.getAttribute("src")) ?? "";
    expect(src).toMatch(/^\/_next\/image\?url=%2Fmedia%2F/);
    const res = await page.request.get(src);
    expect(res.status()).toBe(200);
  });

  test("product rail links to product pages and shows prices", async ({ page }) => {
    await page.goto("/");
    const rail = page.locator("[data-section=product_rail]").first();
    await rail.scrollIntoViewIfNeeded();
    const card = rail.locator("article").first();
    await expect(card.getByRole("link")).toHaveAttribute("href", /^\/products\//);
    await expect(card).toContainText("₹");
  });

  test("skip link moves focus to main content", async ({ page, isMobile }) => {
    test.skip(isMobile, "keyboard flow checked on desktop");
    await page.goto("/");
    await page.keyboard.press("Tab");
    const skip = page.getByRole("link", { name: "Skip to content" });
    await expect(skip).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/#main$/);
  });

  test("no console errors or failed requests", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    page.on("pageerror", (e) => errors.push(e.message));
    page.on(
      "response",
      (r) => r.status() >= 400 && !r.url().includes("/favicon") && errors.push(`${r.status()} ${r.url()}`),
    );
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    expect(errors).toEqual([]);
  });

  test("unknown URLs render the branded 404 inside the storefront chrome", async ({ page }) => {
    const res = await page.goto("/definitely-not-a-page");
    expect(res?.status()).toBe(404);
    await expect(page.getByRole("heading", { level: 1, name: "A loose thread" })).toBeVisible();
    await expect(page.getByRole("banner")).toBeVisible();
  });
});
