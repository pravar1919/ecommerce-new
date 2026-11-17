import type { MetadataRoute } from "next";

/** Phase 3: homepage only. Category, collection and product URLs are added with their pages (Phase 4). */
export default function sitemap(): MetadataRoute.Sitemap {
  const site = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:8080";
  return [{ url: `${site}/`, changeFrequency: "daily", priority: 1 }];
}
