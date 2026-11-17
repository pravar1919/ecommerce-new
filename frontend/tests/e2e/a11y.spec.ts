import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { scrollThrough } from "./helpers";

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

test.describe("accessibility (axe, WCAG 2.2 AA)", () => {
  test("homepage has no violations", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" }); // final visual state, no mid-animation opacity
    await page.goto("/");
    await scrollThrough(page);
    const results = await new AxeBuilder({ page }).withTags(TAGS).analyze();
    expect(results.violations.map((v) => `${v.id}: ${v.nodes.length} × ${v.help}`)).toEqual([]);
  });

  test("open navigation has no violations", async ({ page, isMobile }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    if (isMobile) await page.getByRole("button", { name: "Open menu" }).click();
    else await page.getByRole("navigation", { name: "Main" }).getByRole("button", { name: "Kurtas" }).click();
    await page.waitForTimeout(400);
    const results = await new AxeBuilder({ page })
      .withTags(TAGS)
      // Radix NavigationMenu's focus proxy: an empty aria-hidden span that only forwards Tab from an
      // open trigger into its panel (rendered in the viewport). Focus never rests on it.
      .exclude('nav[aria-label="Main"] li > span[aria-hidden="true"][tabindex="0"]')
      .analyze();
    expect(results.violations.map((v) => `${v.id}: ${v.nodes.length} × ${v.help}`)).toEqual([]);
  });

  test("touch targets in the header are at least 44px", async ({ page, isMobile }) => {
    test.skip(!isMobile, "touch only");
    await page.goto("/");
    const boxes = await page.locator("header a, header button").evaluateAll((els) =>
      els
        .filter((e) => (e as HTMLElement).offsetParent !== null)
        .map((e) => e.getBoundingClientRect())
        .map((r) => Math.min(r.width, r.height)),
    );
    expect(Math.min(...boxes)).toBeGreaterThanOrEqual(44);
  });
});
