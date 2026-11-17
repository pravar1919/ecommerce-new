import Link from "next/link";

import { CmsImage } from "@/components/media/cms-image";
import type { BlockOf } from "@/lib/api/types";
import { routes } from "@/lib/routes";
import { cn } from "@/lib/utils";

import { Section, SectionHeading, sectionId } from "./section";

/**
 * Asymmetric mosaic: a dominant first tile (6 cols) beside a 2×2 of the rest on desktop;
 * a swipeable row on mobile. Never a repeated three-up card row.
 */
export function CategoryMosaic({ block }: { block: BlockOf<"category_grid"> }) {
  const { config } = block;
  const id = sectionId(block.id);
  const [lead, ...rest] = config.items;
  return (
    <Section type="category_grid" labelledBy={id} className="container-page py-section">
      <SectionHeading id={id} eyebrow={config.eyebrow} title={config.title} />
      <ul className="-mx-[var(--page-margin)] mt-10 no-scrollbar flex snap-x snap-mandatory gap-gutter overflow-x-auto px-[var(--page-margin)] md:mx-0 md:grid md:grid-cols-12 md:overflow-visible md:px-0">
        {[lead, ...rest].map((item, i) => (
          <li
            key={item.category.id}
            data-reveal
            suppressHydrationWarning
            style={{ ["--i" as string]: i }}
            className={cn(
              "w-[72vw] shrink-0 snap-start md:w-auto",
              i === 0 ? "md:col-span-6 md:row-span-2" : "md:col-span-3",
              i > 4 && "md:hidden",
            )}
          >
            <Link href={routes.category(item.category.path)} className="group block">
              <div className="overflow-hidden">
                <CmsImage
                  media={item.media}
                  ratio="4/5"
                  sizes={i === 0 ? "(min-width: 768px) 50vw, 72vw" : "(min-width: 768px) 25vw, 72vw"}
                  imgClassName="transition-transform duration-(--dur-cinematic) ease-out-expo group-hover:scale-[1.03] motion-reduce:transition-none"
                />
              </div>
              <div className="mt-3 flex items-baseline justify-between gap-4">
                <h3 className={cn("font-display", i === 0 ? "text-display-md" : "text-heading")}>
                  {item.label}
                </h3>
                <span aria-hidden className="eyebrow text-text-muted transition-colors group-hover:text-text">
                  Shop
                </span>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </Section>
  );
}
