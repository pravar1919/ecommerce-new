import { describe, expect, it } from "vitest";

import { fallbackBrand, resolveBrand, showDevPill, themeKey } from "@/config/brand";
import type { SiteSettings } from "@/lib/api/types";

const settings = (over: Partial<SiteSettings> = {}) =>
  ({
    brand_name: "House",
    tagline: "Tag",
    monogram: "",
    theme_key: "heirloom",
    is_dev_identity: false,
    environment: "production",
    ...over,
  }) as SiteSettings;

describe("brand config", () => {
  it("falls back to the env/dev identity when the CMS is unavailable", () => {
    expect(resolveBrand(null)).toBe(fallbackBrand);
    expect(fallbackBrand.name).toBe("ATELIER");
    expect(showDevPill(fallbackBrand)).toBe(true);
  });
  it("uses CMS settings and hides the DEV pill only for an approved identity in production", () => {
    const brand = resolveBrand(settings());
    expect(brand.name).toBe("House");
    expect(showDevPill(brand)).toBe(false);
    expect(showDevPill(resolveBrand(settings({ environment: "staging" })))).toBe(true);
    expect(showDevPill(resolveBrand(settings({ is_dev_identity: true })))).toBe(true);
  });
  it("only accepts known theme keys", () => {
    expect(themeKey("heirloom")).toBe("heirloom");
    expect(themeKey("neon")).toBe("heirloom");
    expect(themeKey(undefined)).toBe("heirloom");
  });
});
