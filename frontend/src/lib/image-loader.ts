import type { ImageLoaderProps } from "next/image";

const UNSPLASH = "https://images.unsplash.com/";

/**
 * Global next/image loader (next.config `images.loaderFile`).
 * - Unsplash demo stock is hotlinked, as the Unsplash API guidelines require: their imgix CDN
 *   resizes and picks AVIF/WebP itself, so it never passes through our optimiser.
 * - Everything else goes through the built-in optimiser at /_next/image, as before.
 */
export default function imageLoader({ src, width, quality }: ImageLoaderProps): string {
  const q = quality ?? 75;
  if (src.startsWith(UNSPLASH)) {
    const url = new URL(src);
    url.searchParams.set("w", String(width));
    url.searchParams.set("q", String(q));
    url.searchParams.set("auto", "format");
    url.searchParams.set("fit", "max");
    return url.toString();
  }
  return `/_next/image?url=${encodeURIComponent(src)}&w=${width}&q=${q}`;
}
