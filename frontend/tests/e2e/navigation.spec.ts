import { expect, test } from "@playwright/test";

test.describe("desktop mega-menu", () => {
  test.skip(({ isMobile }) => isMobile, "desktop only");

  test("opens by keyboard, lists sub-categories and closes with Escape", async ({ page }) => {
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: "Main" });
    const trigger = nav.getByRole("button", { name: "Kurtas" });
    await trigger.focus();
    await page.keyboard.press("Enter");
    await expect(trigger).toHaveAttribute("aria-expanded", "true");
    await expect(nav.getByRole("link", { name: "All Kurtas" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Kurta Sets" })).toHaveAttribute("href", "/kurtas/kurta-sets");
    await expect(nav.getByRole("link", { name: /Sangeet Nights/ }).first()).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(trigger).toHaveAttribute("aria-expanded", "false");
    await expect(trigger).toBeFocused();
  });

  test("opens on hover", async ({ page }) => {
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: "Main" });
    await nav.getByRole("button", { name: "Sherwanis" }).hover();
    await expect(nav.getByRole("link", { name: "All Sherwanis" })).toBeVisible();
  });
});

test.describe("mobile navigation", () => {
  test.skip(({ isMobile }) => !isMobile, "mobile only");

  test("drawer traps focus and restores it to the menu button", async ({ page }) => {
    await page.goto("/");
    const open = page.getByRole("button", { name: "Open menu" });
    await open.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: "Kurtas" }).click();
    await expect(dialog.getByRole("link", { name: "Kurta Sets" })).toBeVisible();
    for (let i = 0; i < 25; i++) await page.keyboard.press("Tab");
    expect(await dialog.evaluate((d) => d.contains(document.activeElement))).toBe(true);
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(open).toBeFocused();
  });
});

test("announcement bar can be paused", async ({ page }) => {
  await page.goto("/");
  const bar = page.getByRole("region", { name: "Announcements" });
  await bar.getByRole("button", { name: "Pause announcements" }).click();
  await expect(bar.getByRole("button", { name: "Resume announcements" })).toBeVisible();
});
