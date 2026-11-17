import type { components } from "./schema";

type S = components["schemas"];

export type SiteSettings = S["SiteSettingsOut"];
export type Navigation = S["NavigationOut"];
export type NavItem = S["NavItemOut"];
export type Page = S["PageOut"];
export type Block = S["Block"];
export type BlockType = Block["type"];
export type BlockOf<T extends BlockType> = Extract<Block, { type: T }>;
export type Media = S["MediaOut"];
export type Link = S["LinkOut"];
export type ProductCard = S["ProductCard"];
export type ProductImage = S["Image"];
export type Price = S["Price"];
export type Accent = "burgundy" | "emerald" | "royal" | "charcoal";

export type ApiError = {
  error: {
    code: string;
    message: string;
    request_id?: string;
    details?: Record<string, unknown>;
    fields?: Record<string, string[]>;
  };
};
