import { expect, test } from "@playwright/test";

test.describe("reduced motion", () => {
  test.use({ reducedMotion: "reduce" });

  test("nothing is hidden, nothing autoplays, no animations run", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("data-motion", "reduce");
    // every reveal target is fully visible without scrolling
    const hidden = await page
      .locator("[data-reveal]")
      .evaluateAll((els) => els.filter((e) => getComputedStyle(e).opacity !== "1").length);
    expect(hidden).toBe(0);
    // hero: no autoplay control, and the slide does not change on its own
    const hero = page.locator("[data-section=hero]");
    await expect(hero.getByRole("button", { name: /slideshow/ })).toHaveCount(0);
    await expect(hero.getByText("1 / 2")).toBeVisible();
    await page.waitForTimeout(8000);
    await expect(hero.getByText("1 / 2")).toBeVisible();
    // no CSS/WAAPI animations are still running (reduced-motion durations are ~0)
    const running = await page.evaluate(
      () =>
        document
          .getAnimations()
          .filter((a) => a.playState === "running" && Number(a.effect?.getTiming().duration) > 50).length,
    );
    expect(running).toBe(0);
    // React Bits (GSAP) chunks are never requested
    const gsap = await page.evaluate(() =>
      performance.getEntriesByType("resource").some((r) => /gsap|SplitText/i.test(r.name)),
    );
    expect(gsap).toBe(false);
  });
});

test.describe("motion allowed", () => {
  test.use({ reducedMotion: "no-preference" });

  test("below-the-fold content reveals on scroll and is in the DOM before it", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("data-motion", "ok");
    const craft = page.locator("[data-section=craft_story]");
    await expect(craft).toContainText("The hand is the luxury"); // in DOM (SSR) before reveal
    const stat = craft.locator("[data-reveal]").last();
    expect(await stat.evaluate((e) => e.hasAttribute("data-revealed"))).toBe(false);
    await stat.scrollIntoViewIfNeeded();
    await expect(stat).toHaveAttribute("data-revealed", "");
    await expect.poll(() => stat.evaluate((e) => getComputedStyle(e).opacity)).toBe("1");
  });
});
