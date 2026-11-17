import { CmsImage } from "@/components/media/cms-image";
import { SplitHeading } from "@/components/motion/split-heading";
import type { BlockOf } from "@/lib/api/types";
import { cn } from "@/lib/utils";

import { ArrowLink, sectionId } from "./section";

/** Asymmetric 7/5 (or 5/7) editorial pair; "overlap" lets the headline cross the image edge. */
export function EditorialSplit({ block }: { block: BlockOf<"editorial_split"> }) {
  const { config } = block;
  const id = sectionId(block.id);
  const [main, second] = config.media;
  const mirrored = config.layout === "5_7";
  const overlap = config.layout === "overlap";
  return (
    <section data-section="editorial_split" aria-labelledby={id} className="container-page py-section">
      <div className="grid-editorial items-end gap-y-10">
        <div
          data-reveal
          suppressHydrationWarning
          className={cn("col-span-4 md:col-span-5 lg:col-span-7", mirrored && "lg:order-2 lg:col-start-6")}
        >
          <CmsImage
            media={main}
            ratio="3/4"
            sizes="(min-width: 1024px) 58vw, (min-width: 768px) 62vw, 100vw"
          />
        </div>
        <div
          className={cn(
            "col-span-4 md:col-span-3 lg:col-span-4",
            mirrored ? "lg:order-1 lg:col-start-1" : "lg:col-start-9",
            overlap && "relative z-[2] lg:col-span-5 lg:col-start-7",
          )}
        >
          {second && (
            <div data-reveal suppressHydrationWarning className="mb-10 w-2/3 max-md:hidden">
              <CmsImage media={second} ratio="2/3" sizes="(min-width: 1024px) 22vw, 25vw" />
            </div>
          )}
          {config.eyebrow && (
            <p className="eyebrow text-text-muted" data-reveal suppressHydrationWarning>
              {config.eyebrow}
            </p>
          )}
          <div id={id}>
            <SplitHeading
              text={config.headline}
              className={cn(
                "mt-4 font-display text-display-lg",
                overlap && "lg:-ml-[calc(100%/5+var(--gutter))] lg:bg-bg lg:py-4",
              )}
            />
          </div>
          <span
            aria-hidden
            data-reveal="thread"
            suppressHydrationWarning
            className="thread mt-6 w-16 text-ornament"
          />
          <p className="mt-6 max-w-prose text-body-lg text-text-muted" data-reveal suppressHydrationWarning>
            {config.body}
          </p>
          {config.cta && <ArrowLink link={config.cta} className="mt-8" />}
        </div>
      </div>
    </section>
  );
}
