import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const site = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:8080";
  if (process.env.NEXT_PUBLIC_ENVIRONMENT !== "production") {
    return { rules: [{ userAgent: "*", disallow: "/" }] };
  }
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/account", "/cart", "/checkout", "/admin", "/api/"] }],
    sitemap: `${site}/sitemap.xml`,
  };
}
