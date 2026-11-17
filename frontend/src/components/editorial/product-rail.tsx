import { ProductCard } from "@/components/commerce/product-card";
import { LookbookIsland } from "@/components/lookbook/lookbook-island";
import type { BlockOf } from "@/lib/api/types";
import { toLite } from "@/lib/product-lite";
import { routes } from "@/lib/routes";
import { cn } from "@/lib/utils";

import { RailScroller } from "./rail-scroller";
import { Section, SectionHeading, sectionId } from "./section";

/**
 * Product rail. A collection edit with enough pieces is presented as a depth lookbook (the rail
 * is its server-rendered, no-JS form); other sources stay a swipeable rail.
 */
export function ProductRail({ block }: { block: BlockOf<"product_rail"> }) {
  const { config } = block;
  const id = sectionId(block.id);
  const cta =
    config.cta ??
    (config.collection_slug
      ? { label: "View the edit", href: routes.collection(config.collection_slug) }
      : null);
  const lookbook = config.source === "collection" && config.products.length >= 3;

  const rail = (
    <RailScroller label={config.title}>
      {config.products.map((p, i) => (
        <li
          key={p.id}
          className="w-[68vw] shrink-0 snap-start sm:w-[42vw] md:w-[30vw] lg:w-[calc((100%-3*var(--gutter))/4)]"
          data-reveal
          suppressHydrationWarning
          style={{ ["--i" as string]: Math.min(i, 7) }}
        >
          <ProductCard
            product={p}
            sizes="(min-width: 1440px) 340px, (min-width: 1024px) 24vw, (min-width: 768px) 30vw, 68vw"
          />
        </li>
      ))}
    </RailScroller>
  );

  return (
    <Section
      type="product_rail"
      labelledBy={id}
      className={cn(
        lookbook &&
          "bg-[linear-gradient(180deg,var(--bg),color-mix(in_srgb,var(--sand-200),var(--bg)_55%)_55%,var(--bg))]",
      )}
    >
      <div className="container-page py-section-sm">
        <SectionHeading id={id} eyebrow={config.eyebrow} title={config.title} cta={cta} />
        <div className="mt-10">
          {lookbook ? (
            <LookbookIsland products={config.products.map(toLite)} label={config.title}>
              {rail}
            </LookbookIsland>
          ) : (
            rail
          )}
        </div>
      </div>
    </Section>
  );
}
