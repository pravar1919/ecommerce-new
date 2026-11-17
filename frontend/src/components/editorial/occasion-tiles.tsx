import Link from "next/link";

import { CmsImage } from "@/components/media/cms-image";
import type { BlockOf } from "@/lib/api/types";
import { routes } from "@/lib/routes";

import { Section, SectionHeading, sectionId } from "./section";

export function OccasionTiles({ block }: { block: BlockOf<"occasion_tiles"> }) {
  const { config } = block;
  const id = sectionId(block.id);
  return (
    <Section type="occasion_tiles" labelledBy={id} className="container-page py-section">
      <SectionHeading
        id={id}
        eyebrow={config.eyebrow}
        title={config.title || "Shop by occasion"}
        align="center"
      />
      <ul className="mt-12 grid grid-cols-2 gap-gutter gap-y-8 md:grid-cols-3 lg:grid-cols-6">
        {config.items.map((item, i) => (
          <li
            key={item.occasion.id}
            data-reveal
            suppressHydrationWarning
            style={{ ["--i" as string]: i }}
            className={i % 2 ? "lg:mt-16" : undefined}
          >
            <Link href={routes.occasion(item.occasion.slug)} className="group block text-center">
              <div className="overflow-hidden">
                <CmsImage
                  media={item.media}
                  ratio="3/4"
                  sizes="(min-width: 1024px) 16vw, (min-width: 768px) 33vw, 50vw"
                  imgClassName="transition-transform duration-(--dur-cinematic) ease-out-expo group-hover:scale-[1.04] motion-reduce:transition-none"
                />
              </div>
              <h3 className="mt-4 font-display text-heading italic">{item.label}</h3>
              <span
                aria-hidden
                className="mx-auto mt-2 block h-px w-0 bg-current transition-[width] duration-(--dur-base) ease-out-expo group-hover:w-10"
              />
            </Link>
          </li>
        ))}
      </ul>
    </Section>
  );
}
