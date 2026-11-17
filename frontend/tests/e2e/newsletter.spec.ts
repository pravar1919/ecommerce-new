import { expect, test } from "@playwright/test";

const MAILPIT = process.env.MAILPIT_URL ?? "http://localhost:8025";

test("newsletter double opt-in: signup → confirmation email → confirm", async ({ page, request }, info) => {
  test.skip(info.project.name !== "desktop-chromium", "one end-to-end run is enough (shared inbox)");
  const email = `e2e-${Date.now()}@example.com`;

  await page.goto("/");
  const section = page.locator("[data-section=newsletter]");
  await section.scrollIntoViewIfNeeded();
  await section.getByLabel("Email address").fill(email);
  await section.getByRole("checkbox").check();
  await section.getByRole("button", { name: "Subscribe" }).click();
  await expect(section.getByRole("status")).toContainText("Check your inbox to confirm");

  // The worker sends via Mailpit; find the message and its link.
  let link = "";
  await expect
    .poll(
      async () => {
        const search = await request.get(
          `${MAILPIT}/api/v1/search?query=${encodeURIComponent(`to:${email}`)}`,
        );
        const { messages } = await search.json();
        if (!messages?.length) return false;
        const msg = await (await request.get(`${MAILPIT}/api/v1/message/${messages[0].ID}`)).json();
        link = (msg.Text as string).match(/https?:\/\/\S+newsletter\/confirm\?token=\S+/)?.[0] ?? "";
        return Boolean(link);
      },
      { timeout: 20_000 },
    )
    .toBe(true);

  await page.goto(new URL(link).pathname + new URL(link).search);
  await expect(page.getByRole("heading", { name: "Confirm your subscription" })).toBeVisible();
  await page.getByRole("button", { name: "Confirm subscription" }).click();
  await expect(page.getByRole("heading", { name: "You're subscribed" })).toBeFocused();
});
