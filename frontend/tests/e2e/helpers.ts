import type { Page } from "@playwright/test";

export const HOME_SECTIONS = [
  "announcement",
  "header",
  "hero",
  "category_grid",
  "showroom",
  "product_rail",
  "collection_feature",
  "occasion_tiles",
  "editorial_split",
  "product_rail",
  "craft_story",
  "testimonials",
  "instagram_gallery",
  "newsletter",
  "footer",
];

export async function sectionOrder(page: Page): Promise<string[]> {
  return page
    .locator("[data-section]")
    .evaluateAll((els) => els.map((e) => (e as HTMLElement).dataset.section!));
}

export async function isMobile(page: Page) {
  return (page.viewportSize()?.width ?? 1440) < 1024;
}

/** Scroll through the page so lazy images and reveals settle (axe/visual checks see final state). */
export async function scrollThrough(page: Page) {
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += window.innerHeight * 0.8) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 120));
    }
    window.scrollTo(0, 0);
  });
}

/** The homepage hero is immersive: the site chrome slides in only once the visitor scrolls. */
export async function revealHeader(page: Page) {
  await page.evaluate(() => window.scrollTo(0, 400));
  await page.locator('[data-chrome="immersive"][data-revealed="true"]').waitFor();
  // let the slide-in transition settle before pointer interactions
  await page.waitForTimeout(700);
}
