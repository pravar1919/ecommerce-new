import { CmsImage } from "@/components/media/cms-image";
import type { BlockOf } from "@/lib/api/types";
import { cn } from "@/lib/utils";

import { ArrowLink, Section, sectionId } from "./section";

/** Mixed-span square gallery. Links to the profile only once the brand's handle is configured. */
export function InstagramGallery({ block }: { block: BlockOf<"instagram_gallery"> }) {
  const { config } = block;
  const id = sectionId(block.id);
  return (
    <Section type="instagram_gallery" labelledBy={id} className="py-section-sm">
      <div className="container-page flex flex-wrap items-end justify-between gap-4">
        <h2 id={id} className="font-display text-display-lg">
          {config.title || "Gallery"}
        </h2>
        {config.profile_url && config.handle && (
          <ArrowLink link={{ label: `Follow ${config.handle}`, href: config.profile_url }} />
        )}
      </div>
      <ul className="container-page mt-10 grid grid-cols-2 gap-1 md:grid-cols-5">
        {config.media.slice(0, 7).map((m, i) => (
          <li
            key={m.id}
            data-reveal
            suppressHydrationWarning
            style={{ ["--i" as string]: i }}
            className={cn(i === 0 && "col-span-2 row-span-2")}
          >
            <CmsImage
              media={m}
              ratio="1/1"
              sizes={i === 0 ? "(min-width: 768px) 40vw, 100vw" : "(min-width: 768px) 20vw, 50vw"}
            />
          </li>
        ))}
      </ul>
    </Section>
  );
}
