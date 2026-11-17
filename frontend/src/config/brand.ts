import type { SiteSettings } from "@/lib/api/types";

/**
 * Brand identity is data (docs/brand-identity.md): resolved from GET /cms/site-settings/, with
 * NEXT_PUBLIC_BRAND_* as a build-time fallback. No brand name is hardcoded in components.
 */
export type ThemeKey = "heirloom" | "dev";

export type BrandConfig = {
  name: string;
  tagline: string;
  monogram: string;
  theme: ThemeKey;
  isDevIdentity: boolean;
  environment: string;
};

const THEMES: ThemeKey[] = ["heirloom", "dev"];
const DEV_BRAND_NAME = "ATELIER";

export function themeKey(value: string | undefined | null): ThemeKey {
  return THEMES.includes(value as ThemeKey) ? (value as ThemeKey) : "heirloom";
}

export const fallbackBrand: BrandConfig = {
  name: process.env.NEXT_PUBLIC_BRAND_NAME || DEV_BRAND_NAME,
  tagline: process.env.NEXT_PUBLIC_BRAND_TAGLINE || "",
  monogram: "",
  theme: themeKey(process.env.NEXT_PUBLIC_BRAND_THEME),
  isDevIdentity: (process.env.NEXT_PUBLIC_BRAND_NAME || DEV_BRAND_NAME) === DEV_BRAND_NAME,
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT || "development",
};

export function resolveBrand(settings: SiteSettings | null): BrandConfig {
  if (!settings) return fallbackBrand;
  return {
    name: settings.brand_name || fallbackBrand.name,
    tagline: settings.tagline,
    monogram: settings.monogram,
    theme: themeKey(settings.theme_key),
    isDevIdentity: settings.is_dev_identity,
    environment: settings.environment,
  };
}

/** The "DEV" pill shows for the temporary identity, and in any non-production environment. */
export function showDevPill(brand: BrandConfig): boolean {
  return brand.isDevIdentity || brand.environment !== "production";
}
