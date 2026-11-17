/**
 * Public media URLs from the API point at the object store (MEDIA_PUBLIC_BASE_URL). The storefront
 * serves them same-origin under /media/* (next.config rewrite), so next/image can optimise them
 * without allow-listing storage hosts, and production can swap in a CDN by changing env only.
 */
export const MEDIA_PREFIX = "/media/";

export function toSameOriginMedia(url: string, publicBase: string | undefined): string {
  if (!publicBase) return url;
  const base = publicBase.replace(/\/+$/, "") + "/";
  return url.startsWith(base) ? MEDIA_PREFIX + url.slice(base.length) : url;
}

/** Deep-rewrite every string field that is a public media URL. */
export function rewriteMediaUrls<T>(value: T, publicBase: string | undefined): T {
  if (!publicBase) return value;
  const walk = (v: unknown): unknown => {
    if (typeof v === "string") return toSameOriginMedia(v, publicBase);
    if (Array.isArray(v)) return v.map(walk);
    if (v && typeof v === "object") {
      return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, walk(x)]));
    }
    return v;
  };
  return walk(value) as T;
}

/** CSS object-position from a 0–1 focal point, so art-directed crops keep the subject in frame. */
export function focalPosition(x = 0.5, y = 0.5): string {
  const clamp = (n: number) => Math.min(1, Math.max(0, n));
  return `${Math.round(clamp(x) * 100)}% ${Math.round(clamp(y) * 100)}%`;
}
