import Link from "next/link";

import { CmsImage } from "@/components/media/cms-image";
import { FilmGrain } from "@/components/motion/film-grain";
import { SplitHeading } from "@/components/motion/split-heading";
import { Button } from "@/components/ui/button";
import type { BlockOf } from "@/lib/api/types";
import { routes } from "@/lib/routes";
import { cn } from "@/lib/utils";

import { sectionId } from "./section";

/** Campaign band in the collection's own accent; images overlap the text panel by one column. */
export function CollectionFeature({ block }: { block: BlockOf<"collection_feature"> }) {
  const { config } = block;
  const id = sectionId(block.id);
  const [main, detail] = config.media;
  const right = config.layout === "split_right";
  const full = config.layout === "full_bleed";

  if (full) {
    return (
      <section
        data-section="collection_feature"
        aria-labelledby={id}
        data-accent={config.collection.accent}
        className="relative"
      >
        <CmsImage media={main} ratio="21/9" sizes="100vw" className="max-md:aspect-[4/5]!" />
        <div className="absolute inset-0 bg-[rgb(36_35_35/0.3)]" aria-hidden />
        <div className="container-page absolute inset-x-0 bottom-0 pb-12 text-text-inverse">
          <FeatureCopy config={config} id={id} inverse />
        </div>
      </section>
    );
  }

  return (
    <section
      data-section="collection_feature"
      aria-labelledby={id}
      data-accent={config.collection.accent}
      className="relative overflow-hidden bg-accent text-accent-fg"
    >
      <FilmGrain opacity={0.05} />
      <div className="container-page grid-editorial relative z-[2] items-center gap-y-12 py-section-sm">
        <div
          className={cn(
            "relative col-span-4 md:col-span-4 lg:col-span-7",
            right && "lg:order-2 lg:col-start-6",
          )}
        >
          <div data-reveal suppressHydrationWarning>
            <CmsImage
              media={main}
              ratio="4/5"
              sizes="(min-width: 1024px) 50vw, (min-width: 768px) 50vw, 100vw"
              className="lg:w-[78%]"
              imgClassName="parallax-img"
            />
          </div>
          {detail && (
            <div
              data-reveal
              suppressHydrationWarning
              style={{ ["--i" as string]: 2 }}
              className={cn("absolute -bottom-10 w-[44%] max-lg:hidden", right ? "left-0" : "right-0")}
            >
              <CmsImage media={detail} ratio="2/3" sizes="20vw" />
            </div>
          )}
        </div>
        <div
          className={cn(
            "col-span-4 md:col-span-4 lg:col-span-4",
            right ? "lg:order-1 lg:col-start-1" : "lg:col-start-9",
          )}
        >
          <FeatureCopy config={config} id={id} inverse />
        </div>
      </div>
    </section>
  );
}

function FeatureCopy({
  config,
  id,
  inverse,
}: {
  config: BlockOf<"collection_feature">["config"];
  id: string;
  inverse?: boolean;
}) {
  return (
    <div>
      {config.eyebrow && <p className="eyebrow opacity-80">{config.eyebrow}</p>}
      <div id={id}>
        <SplitHeading text={config.headline} className="mt-4 font-display text-display-xl" />
      </div>
      <span
        aria-hidden
        data-reveal="thread"
        suppressHydrationWarning
        className="thread mt-6 w-20 text-ornament"
      />
      {config.body && (
        <p className="mt-6 max-w-md text-body-lg text-current/90" data-reveal suppressHydrationWarning>
          {config.body}
        </p>
      )}
      <Button asChild variant={inverse ? "inverse" : "primary"} className="mt-10">
        <Link href={routes.collection(config.collection.slug)}>{config.cta_label}</Link>
      </Button>
    </div>
  );
}
