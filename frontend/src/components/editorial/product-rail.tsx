import { ProductCard } from "@/components/commerce/product-card";
import type { BlockOf } from "@/lib/api/types";
import { routes } from "@/lib/routes";

import { RailScroller } from "./rail-scroller";
import { Section, SectionHeading, sectionId } from "./section";

export function ProductRail({ block }: { block: BlockOf<"product_rail"> }) {
  const { config } = block;
  const id = sectionId(block.id);
  const cta =
    config.cta ??
    (config.collection_slug
      ? { label: "View the edit", href: routes.collection(config.collection_slug) }
      : null);
  return (
    <Section type="product_rail" labelledBy={id} className="container-page py-section-sm">
      <SectionHeading id={id} eyebrow={config.eyebrow} title={config.title} cta={cta} />
      <div className="mt-10">
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
      </div>
    </Section>
  );
}
