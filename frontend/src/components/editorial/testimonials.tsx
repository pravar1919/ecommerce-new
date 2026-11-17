import { BlurQuote } from "@/components/motion/blur-quote";
import type { BlockOf } from "@/lib/api/types";

import { Section, SectionHeading, sectionId } from "./section";

/** Real customer quotes only. Dev placeholders are visibly labelled. */
export function Testimonials({ block }: { block: BlockOf<"testimonials"> }) {
  const { config } = block;
  const id = sectionId(block.id);
  return (
    <Section type="testimonials" labelledBy={id} className="container-page py-section">
      <SectionHeading id={id} eyebrow={config.eyebrow} title={config.title || "In their words"} />
      <ul className="mt-14 grid gap-x-gutter gap-y-14 md:grid-cols-3">
        {config.items.map((t, i) => (
          <li
            key={t.id}
            data-reveal
            suppressHydrationWarning
            style={{ ["--i" as string]: i }}
            className={i === 1 ? "md:mt-20" : undefined}
          >
            <figure>
              <span aria-hidden className="font-display text-display-lg leading-none text-primary">
                “
              </span>
              <blockquote>
                <BlurQuote text={t.quote} className="font-display text-display-md" />
              </blockquote>
              <figcaption className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-2 text-body text-text-muted">
                <span className="eyebrow text-text">{t.name}</span>
                {t.occasion && <span>{t.occasion}</span>}
                {t.location && <span>{t.location}</span>}
                {t.is_placeholder && (
                  <span className="rounded-pill border px-2 py-0.5 text-caption">
                    Placeholder, not a real customer
                  </span>
                )}
              </figcaption>
            </figure>
          </li>
        ))}
      </ul>
    </Section>
  );
}
