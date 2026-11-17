import type { BlockOf } from "@/lib/api/types";

/** HTML is sanitised server-side (nh3 allow-list in apps/cms/blocks.py) before it is stored. */
export function RichText({ block }: { block: BlockOf<"rich_text"> }) {
  return (
    <section data-section="rich_text" className="container-page py-section-sm">
      <div
        className="mx-auto max-w-prose space-y-5 text-body-lg [&_a]:underline [&_a]:underline-offset-4 [&_h2]:font-display [&_h2]:text-display-md [&_h3]:font-display [&_h3]:text-heading [&_ol]:list-decimal [&_ol]:pl-6 [&_ul]:list-disc [&_ul]:pl-6"
        dangerouslySetInnerHTML={{ __html: block.config.html }}
      />
    </section>
  );
}
