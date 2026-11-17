import "server-only";

import createClient from "openapi-fetch";
import { cacheLife, cacheTag } from "next/cache";

import { rewriteMediaUrls } from "@/lib/media";

import type { paths } from "./schema";
import { TAGS } from "./tags";
import type { Navigation, Page, SiteSettings } from "./types";

/**
 * Server-side API access. Next.js talks to Django inside the network (INTERNAL_API_URL),
 * never through the public origin. Public CMS reads are cached with `use cache` + tags and
 * revalidated on publish (Django → /api/revalidate). A failed read is cached only briefly
 * (`seconds` → a dynamic hole), so an outage or a build without the API never pins fallback
 * content into the static shell.
 */
const api = createClient<paths>({
  baseUrl: process.env.INTERNAL_API_URL ?? "http://localhost:8000",
});

const TIMEOUT_MS = 5000;

async function read<T>(
  promise: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T | null> {
  try {
    const { data, response } = await promise;
    if (!response.ok || data === undefined) return null;
    return rewriteMediaUrls(data, process.env.MEDIA_PUBLIC_BASE_URL);
  } catch {
    return null;
  }
}

const opts = () => ({ signal: AbortSignal.timeout(TIMEOUT_MS) });

export async function getSiteSettings(): Promise<SiteSettings | null> {
  "use cache";
  cacheTag(TAGS.siteSettings);
  const data = await read(api.GET("/api/v1/cms/site-settings/", opts()));
  if (data) cacheLife("hours");
  else cacheLife("seconds");
  return data;
}

export async function getNavigation(): Promise<Navigation | null> {
  "use cache";
  cacheTag(TAGS.navigation, "catalog:categories");
  const data = await read(api.GET("/api/v1/cms/navigation/", opts()));
  if (data) cacheLife("hours");
  else cacheLife("seconds");
  return data;
}

/** null = not found or unavailable; callers decide between notFound() and a fallback. */
export async function getPage(slug: string): Promise<{ page: Page | null; status: number }> {
  "use cache";
  cacheTag(TAGS.page(slug), "catalog:products");
  try {
    const { data, response } = await api.GET("/api/v1/cms/pages/{slug}/", {
      params: { path: { slug } },
      ...opts(),
    });
    if (response.ok && data) {
      cacheLife("hours");
      return { page: rewriteMediaUrls(data, process.env.MEDIA_PUBLIC_BASE_URL), status: 200 };
    }
    if (response.status === 404) cacheLife("minutes");
    else cacheLife("seconds");
    return { page: null, status: response.status };
  } catch {
    cacheLife("seconds");
    return { page: null, status: 503 };
  }
}
