import type { ProductCard, ProductImage } from "@/lib/api/types";

/**
 * The slice of a product card that interactive islands (salon, lookbook) render. Server
 * components pass this rather than the full card, so the RSC payload hydrated on first load stays
 * small: no hover images, credits, badges or per-colour image objects.
 */
export type ProductLite = Pick<ProductCard, "id" | "slug" | "name" | "price" | "is_mtm_available"> & {
  category: { name: string };
  primary_image: Pick<ProductImage, "url" | "alt" | "focal_x" | "focal_y"> | null;
  colours: { slug: string; name: string; hex: string }[];
};

export function toLite(p: ProductCard): ProductLite {
  const img = p.primary_image;
  return {
    id: p.id,
    slug: p.slug,
    name: p.name,
    price: p.price,
    is_mtm_available: p.is_mtm_available,
    category: { name: p.category.name },
    primary_image: img ? { url: img.url, alt: img.alt, focal_x: img.focal_x, focal_y: img.focal_y } : null,
    colours: p.colours.map((c) => ({ slug: c.slug, name: c.name, hex: c.hex })),
  };
}
