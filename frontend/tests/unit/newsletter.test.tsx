import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, describe, expect, it, vi } from "vitest";

const post = vi.fn();
vi.mock("@/lib/api/client", async (orig) => ({
  ...(await orig<typeof import("@/lib/api/client")>()),
  api: { POST: (...args: unknown[]) => post(...args) },
}));

import { NewsletterSignup } from "@/components/editorial/newsletter-signup";

const renderForm = () =>
  render(
    <NewsletterSignup headingId="nl" headline="New edits, first" consentText="I'd like to receive emails." />,
  );

describe("NewsletterSignup", () => {
  beforeEach(() => post.mockReset());

  it("has no axe violations", async () => {
    const { container } = renderForm();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("validates locally and links errors to fields", async () => {
    const user = userEvent.setup();
    renderForm();
    await user.type(screen.getByLabelText("Email address"), "not-an-email");
    await user.click(screen.getByRole("button", { name: "Subscribe" }));
    const email = screen.getByLabelText("Email address");
    expect(email).toHaveAttribute("aria-invalid", "true");
    expect(email).toHaveAccessibleDescription("Enter a valid email address.");
    expect(screen.getByRole("checkbox")).toHaveAccessibleDescription(/confirm/);
    expect(screen.getByRole("status")).toHaveTextContent("Please check the highlighted fields.");
    expect(post).not.toHaveBeenCalled();
  });

  it("submits consent explicitly and shows the double opt-in message", async () => {
    post.mockResolvedValue({ response: { ok: true, status: 202 }, data: { status: "pending" } });
    const user = userEvent.setup();
    renderForm();
    await user.type(screen.getByLabelText("Email address"), "asha@example.com");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Subscribe" }));
    expect(post).toHaveBeenCalledWith("/api/v1/cms/newsletter/", {
      body: { email: "asha@example.com", consent: true, source: "home" },
    });
    expect(await screen.findByText(/Check your inbox to confirm/)).toBeInTheDocument();
  });

  it("surfaces rate limiting", async () => {
    post.mockResolvedValue({
      response: { ok: false, status: 429 },
      error: { error: { code: "rate_limited", message: "x" } },
    });
    const user = userEvent.setup();
    renderForm();
    await user.type(screen.getByLabelText("Email address"), "asha@example.com");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Subscribe" }));
    expect(await screen.findByText(/Too many attempts/)).toBeInTheDocument();
  });
});
