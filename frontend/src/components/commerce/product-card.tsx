import Image from "next/image";
import Link from "next/link";

import type { ProductCard as ProductCardT } from "@/lib/api/types";
import { focalPosition } from "@/lib/media";
import { routes } from "@/lib/routes";
import { cn } from "@/lib/utils";

import { Price } from "./price";

const BADGE_LABEL: Record<string, string> = {
  new: "New",
  sale: "Sale",
  made_to_measure: "Made to measure",
  sold_out: "Sold out",
};

/**
 * Product card: 4:5 image, no frame, zero radius. The second image cross-reveals with a diagonal
 * clip-path on hover ("fabric hover"). Name in small caps sans, price on its own line.
 */
export function ProductCard({
  product,
  sizes,
  priority = false,
}: {
  product: ProductCardT;
  sizes: string;
  priority?: boolean;
}) {
  const img = product.primary_image;
  const hover = product.hover_image;
  const badges = product.badges.filter((b) => b !== "made_to_measure").slice(0, 2);
  return (
    <article className="group/card relative">
      <Link href={routes.product(product.slug)} className="block">
        <div className="relative aspect-[4/5] overflow-hidden bg-skeleton">
          {img && (
            <Image
              src={img.url}
              alt={img.alt}
              fill
              sizes={sizes}
              priority={priority}
              className="object-cover"
              style={{ objectPosition: focalPosition(img.focal_x, img.focal_y) }}
            />
          )}
          {hover && (
            <Image
              src={hover.url}
              alt=""
              fill
              sizes={sizes}
              loading="lazy"
              className="object-cover transition-[clip-path] duration-(--dur-slow) ease-out-expo [clip-path:polygon(0_0,0_0,0_0,0_0)] group-hover/card:[clip-path:polygon(0_0,100%_0,100%_100%,0_100%)] motion-reduce:transition-none"
              style={{ objectPosition: focalPosition(hover.focal_x, hover.focal_y) }}
            />
          )}
          {badges.length > 0 && (
            <ul className="absolute top-3 left-3 flex flex-col items-start gap-1">
              {badges.map((b) => (
                <li
                  key={b}
                  className={cn(
                    "bg-bg px-2 py-1 text-[0.6875rem] leading-none font-medium tracking-[0.1em] uppercase",
                    b === "sold_out" && "bg-text text-bg",
                  )}
                >
                  {BADGE_LABEL[b] ?? b}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="mt-3 space-y-1 pr-2">
          <h3 className="text-[0.8125rem] leading-snug font-medium tracking-[0.06em] uppercase">
            {product.name}
          </h3>
          <Price price={product.price} />
          <p className="flex items-center gap-2 text-caption text-text-muted">
            {product.colours.length > 1 && (
              <span className="flex items-center gap-1" aria-label={`${product.colours.length} colours`}>
                {product.colours.slice(0, 4).map((c) => (
                  <span
                    key={c.slug}
                    aria-hidden
                    title={c.name}
                    className="size-2.5 rounded-pill border border-[rgb(36_35_35/0.25)]"
                    style={{ backgroundColor: c.hex }}
                  />
                ))}
                <span aria-hidden>{product.colours.length > 4 ? `+${product.colours.length - 4}` : ""}</span>
              </span>
            )}
            {product.is_mtm_available && <span>Made to measure available</span>}
          </p>
        </div>
      </Link>
    </article>
  );
}
