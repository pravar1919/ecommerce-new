import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Price } from "@/components/commerce/price";
import { ProductCard } from "@/components/commerce/product-card";
import { BlockRenderer } from "@/components/editorial/block-renderer";
import { CampaignHero } from "@/components/editorial/campaign-hero";
import { AnnouncementBar } from "@/components/layout/announcement-bar";
import { CountStat } from "@/components/motion/count-stat";
import { Magnetic } from "@/components/motion/magnetic";
import { SplitHeading } from "@/components/motion/split-heading";
import type { Block } from "@/lib/api/types";

import { heroConfig, product } from "./fixtures";
import { media as mq } from "./setup";

beforeEach(() => {
  mq.reducedMotion = false;
});

describe("Price", () => {
  it("shows sale, struck MRP, discount and screen-reader labels", () => {
    render(<Price price={product().price} />);
    expect(screen.getByText("₹88,500")).toBeInTheDocument();
    expect(screen.getByText("₹98,500").closest("s")).not.toBeNull();
    expect(screen.getByText("10% off")).toBeInTheDocument();
    expect(screen.getByText(/Sale price/)).toHaveClass("sr-only");
  });
  it("prefixes ranges with From", () => {
    const p = product().price;
    render(<Price price={{ ...p, has_range: true, on_sale: false }} />);
    expect(screen.getByText("From")).toBeInTheDocument();
    expect(screen.queryByText("₹98,500")).toBeNull();
  });
});

describe("ProductCard", () => {
  it("links to the PDP, labels badges and colours, and has no axe violations", async () => {
    const { container } = render(<ProductCard product={product()} sizes="25vw" />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/products/ivory-sherwani");
    expect(screen.getByText("New")).toBeInTheDocument();
    expect(screen.getByLabelText("2 colours")).toBeInTheDocument();
    expect(screen.getByText("Made to measure available")).toBeInTheDocument();
    expect(screen.getByAltText("Front view")).toBeInTheDocument();
    expect(container.querySelector('img[alt=""]')).not.toBeNull(); // hover image is decorative
    expect(await axe(container)).toHaveNoViolations();
  });
  it("shows sold out", () => {
    render(<ProductCard product={product({ badges: ["sold_out"], in_stock: false })} sizes="25vw" />);
    expect(screen.getByText("Sold out")).toBeInTheDocument();
  });
});

describe("AnnouncementBar", () => {
  const ann = {
    enabled: true,
    accent: "burgundy" as const,
    messages: [
      { text: "First", href: "/a" },
      { text: "Second", href: null },
    ],
  };
  afterEach(() => vi.useRealTimers());

  it("renders nothing when disabled", () => {
    const { container } = render(<AnnouncementBar announcement={{ ...ann, enabled: false }} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("rotates, and the pause control stops rotation (WCAG 2.2.2)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<AnnouncementBar announcement={ann} />);
    const active = () => document.querySelector('[data-active="true"]')?.textContent;
    expect(active()).toBe("First");
    await act(() => vi.advanceTimersByTimeAsync(5100));
    expect(active()).toBe("Second");
    await user.click(screen.getByRole("button", { name: "Pause announcements" }));
    // hovering/focus also pauses; move pointer away to isolate the toggle
    await user.unhover(screen.getByRole("region", { name: "Announcements" }));
    (document.activeElement as HTMLElement | null)?.blur();
    await act(() => vi.advanceTimersByTimeAsync(11000));
    expect(active()).toBe("Second");
    expect(screen.getByRole("button", { name: "Resume announcements" })).toBeInTheDocument();
  });
});

describe("reduced motion fallbacks", () => {
  it("SplitHeading renders a plain, readable heading", () => {
    mq.reducedMotion = true;
    render(<SplitHeading text="Dress for every ceremony" />);
    expect(screen.getByRole("heading", { level: 2, name: "Dress for every ceremony" })).toBeVisible();
  });
  it("CountStat shows the final value immediately", () => {
    mq.reducedMotion = true;
    render(<CountStat value={1234} />);
    expect(screen.getByText("1,234")).toBeInTheDocument();
  });
  it("Magnetic renders children untouched", () => {
    mq.reducedMotion = true;
    render(
      <Magnetic>
        <button type="button">Shop</button>
      </Magnetic>,
    );
    expect(screen.getByRole("button", { name: "Shop" }).parentElement?.tagName).toBe("DIV");
  });
  it("CampaignHero does not autoplay or offer a pause control under reduced motion", () => {
    mq.reducedMotion = true;
    render(<CampaignHero config={heroConfig()} />);
    expect(screen.queryByRole("button", { name: /Pause slideshow/ })).toBeNull();
    expect(screen.getByRole("button", { name: "Next slide" })).toBeInTheDocument();
  });
});

describe("CampaignHero", () => {
  it("is an accessible carousel with one visible slide", async () => {
    const { container } = render(<CampaignHero config={heroConfig()} />);
    expect(screen.getByRole("region", { name: "Featured campaigns" })).toHaveAttribute(
      "aria-roledescription",
      "carousel",
    );
    expect(screen.getByRole("heading", { name: "Headline number 1" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Headline number 2" })).toBeNull();
    expect(screen.getByRole("link", { name: "Shop the edit" })).toHaveAttribute("href", "/collections/x");
    expect(screen.getByRole("button", { name: "Pause slideshow" })).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });
  it("advances with the controls", async () => {
    mq.reducedMotion = true; // instant swap, no curtain timer
    const user = userEvent.setup();
    render(<CampaignHero config={heroConfig()} />);
    await user.click(screen.getByRole("button", { name: "Next slide" }));
    expect(screen.getByRole("heading", { name: "Headline number 2" })).toBeInTheDocument();
    expect(screen.getByText("2 / 2")).toBeInTheDocument();
  });
});

describe("BlockRenderer", () => {
  it("ignores unknown block types", () => {
    const { container } = render(
      <BlockRenderer block={{ id: "x", type: "carousel", config: {} } as unknown as Block} />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
