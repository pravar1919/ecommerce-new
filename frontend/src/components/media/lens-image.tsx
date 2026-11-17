import type { ComponentProps } from "react";

import { CmsImage } from "./cms-image";

type Img = ComponentProps<typeof CmsImage>["media"];

/**
 * An image with a second one beneath it, shown through a soft circle that follows the pointer
 * (globals.css "Lens reveal"). Server-rendered; the hidden layer is decorative (aria-hidden) and
 * never appears on touch or keyboard-only devices, so nothing depends on discovering it.
 */
export function LensImage({
  media,
  reveal,
  sizes,
  ratio,
  hint = "Move to look closer",
  parallax = false,
}: {
  media: Img;
  reveal?: Img;
  sizes: string;
  ratio: string;
  hint?: string;
  parallax?: boolean;
}) {
  const imgClassName = parallax ? "parallax-img" : undefined;
  if (!reveal) return <CmsImage media={media} ratio={ratio} sizes={sizes} imgClassName={imgClassName} />;
  return (
    <div data-lens>
      <CmsImage media={media} ratio={ratio} sizes={sizes} imgClassName={imgClassName} />
      <div aria-hidden className="lens-layer">
        <CmsImage media={{ ...reveal, credit: undefined }} ratio={ratio} sizes={sizes} />
      </div>
      <p
        aria-hidden
        className="lens-hint pointer-events-none absolute bottom-4 left-4 bg-[rgb(36_35_35/0.86)] px-3 py-2 text-caption tracking-[0.08em] text-text-inverse uppercase backdrop-blur-sm"
      >
        {hint}
      </p>
    </div>
  );
}
