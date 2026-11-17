import { CmsImage } from "@/components/media/cms-image";
import { CountStat } from "@/components/motion/count-stat";
import { FilmGrain } from "@/components/motion/film-grain";
import { SplitHeading } from "@/components/motion/split-heading";
import type { BlockOf } from "@/lib/api/types";
import { formatCount, withSuffix } from "@/lib/format";

import { ArrowLink, sectionId } from "./section";

/** Inverse band: gold numerals on charcoal (6.6:1) tell the craft story. */
export function CraftStory({ block }: { block: BlockOf<"craft_story"> }) {
  const { config } = block;
  const id = sectionId(block.id);
  const [main, second] = config.media;
  return (
    <section
      data-section="craft_story"
      aria-labelledby={id}
      className="surface-inverse relative overflow-hidden"
    >
      <FilmGrain opacity={0.07} />
      <div className="container-page grid-editorial relative z-[2] gap-y-12 py-section">
        <div className="col-span-4 md:col-span-8 lg:col-span-6">
          {config.eyebrow && (
            <p className="eyebrow text-ornament" data-reveal suppressHydrationWarning>
              {config.eyebrow}
            </p>
          )}
          <div id={id}>
            <SplitHeading text={config.headline} className="mt-4 font-display text-display-xl" />
          </div>
          <span
            aria-hidden
            data-reveal="thread"
            suppressHydrationWarning
            className="thread mt-6 w-20 text-ornament"
          />
          <p className="mt-8 max-w-xl text-body-lg text-text-muted" data-reveal suppressHydrationWarning>
            {config.body}
          </p>
          {config.cta && <ArrowLink link={config.cta} className="mt-8" />}
        </div>
        <div className="col-span-4 grid grid-cols-2 gap-gutter md:col-span-8 lg:col-span-5 lg:col-start-8">
          <div data-reveal suppressHydrationWarning className="col-span-2">
            <CmsImage media={main} ratio="4/3" sizes="(min-width: 1024px) 40vw, 100vw" />
          </div>
          {second && (
            <div
              data-reveal
              suppressHydrationWarning
              style={{ ["--i" as string]: 1 }}
              className="col-span-1 col-start-2 -mt-24 max-md:hidden"
            >
              <CmsImage media={second} ratio="4/5" sizes="20vw" />
            </div>
          )}
        </div>
        {config.stats.length > 0 && (
          <dl className="col-span-full grid grid-cols-2 gap-x-gutter gap-y-10 border-t pt-12 lg:grid-cols-4">
            {config.stats.map((s, i) => (
              <div key={s.label} data-reveal suppressHydrationWarning style={{ ["--i" as string]: i }}>
                <dt className="sr-only">{s.label}</dt>
                <dd>
                  <span className="sr-only">{withSuffix(formatCount(s.value), s.suffix)}</span>
                  <span aria-hidden className="block">
                    <span className="price block font-display text-display-xl text-ornament">
                      <CountStat value={s.value} />
                      {s.suffix && <span className="ml-2 font-sans text-heading">{s.suffix}</span>}
                    </span>
                    <span className="mt-3 block max-w-[22ch] text-body text-text-muted">{s.label}</span>
                  </span>
                </dd>
              </div>
            ))}
          </dl>
        )}
      </div>
    </section>
  );
}
