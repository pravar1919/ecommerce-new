import type { BlockOf, Media, ProductCard } from "@/lib/api/types";

export const media = (over: Partial<Media> = {}): Media => ({
  id: "m1",
  kind: "image",
  url: "/media/cms/x.png",
  poster_url: null,
  alt: "Groom in an ivory sherwani",
  width: 1600,
  height: 2000,
  focal_x: 0.5,
  focal_y: 0.5,
  dominant_hex: "#651E35",
  blurhash: "",
  credit: "",
  is_placeholder: true,
  ...over,
});

const money = (amount: number, formatted: string) => ({ amount, currency: "INR", formatted });

export const product = (over: Partial<ProductCard> = {}): ProductCard => ({
  id: "p1",
  slug: "ivory-sherwani",
  name: "Ivory Zardozi Sherwani",
  category: { id: "c1", name: "Sherwanis", slug: "sherwanis", path: "sherwanis" },
  price: {
    current: money(8850000, "₹88,500"),
    mrp: money(9850000, "₹98,500"),
    has_range: false,
    on_sale: true,
    discount_percent: 10,
  },
  badges: ["new", "sale", "made_to_measure"],
  primary_image: {
    id: "i1",
    url: "/media/p/1.png",
    alt: "Front view",
    width: 1600,
    height: 2000,
    focal_x: 0.5,
    focal_y: 0.5,
    is_placeholder: true,
  },
  hover_image: {
    id: "i2",
    url: "/media/p/2.png",
    alt: "Back view",
    width: 1600,
    height: 2000,
    focal_x: 0.5,
    focal_y: 0.5,
    is_placeholder: true,
  },
  colours: [
    { slug: "ivory", name: "Ivory", hex: "#F2EBDD", image: null },
    { slug: "champagne", name: "Champagne", hex: "#D9C3A0", image: null },
  ],
  is_mtm_available: true,
  in_stock: true,
  ...over,
});

export const heroConfig = (n = 2): BlockOf<"hero">["config"] => ({
  autoplay_ms: 7000,
  slides: Array.from({ length: n }, (_, i) => ({
    eyebrow: `Edit ${i + 1}`,
    headline: `Headline number ${i + 1}`,
    subline: "Subline",
    media: media({ id: `m${i}` }),
    mobile_media: null,
    cta: { label: "Shop the edit", href: "/collections/x" },
    secondary_cta: null,
    accent: "burgundy",
    theme: "dark",
  })),
});
