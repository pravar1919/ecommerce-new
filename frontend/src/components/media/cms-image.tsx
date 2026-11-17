import Image from "next/image";

import type { Media, ProductImage } from "@/lib/api/types";
import { focalPosition } from "@/lib/media";
import { cn } from "@/lib/utils";

import { PhotoCredit } from "./photo-credit";

type AnyImage = Pick<Media, "url" | "alt" | "width" | "height" | "focal_x" | "focal_y"> &
  Partial<Pick<Media, "dominant_hex" | "credit">>;

type Props = {
  media: AnyImage | ProductImage;
  sizes: string;
  /** Aspect ratio box, e.g. "4/5". Omit when the parent sizes the image (fill). */
  ratio?: string;
  priority?: boolean;
  className?: string;
  imgClassName?: string;
};

/**
 * Responsive image for CMS and product media: fills a ratio box, crops around the stored focal
 * point, shows the asset's dominant colour while loading. Only the LCP image gets `priority`.
 */
export function CmsImage({ media, sizes, ratio, priority = false, className, imgClassName }: Props) {
  const bg = "dominant_hex" in media && media.dominant_hex ? media.dominant_hex : undefined;
  return (
    <div
      className={cn("group/img relative overflow-hidden bg-skeleton", className)}
      style={{ aspectRatio: ratio, backgroundColor: bg }}
    >
      <Image
        src={media.url}
        alt={media.alt}
        fill
        sizes={sizes}
        loading={priority ? "eager" : "lazy"}
        fetchPriority={priority ? "high" : undefined}
        className={cn("object-cover", imgClassName)}
        style={{ objectPosition: focalPosition(media.focal_x, media.focal_y) }}
      />
      <PhotoCredit credit={media.credit} />
    </div>
  );
}
