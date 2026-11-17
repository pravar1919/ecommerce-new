import path from "node:path";

import type { NextConfig } from "next";
import { withCn } from "cn/next";

const internalApi = process.env.INTERNAL_API_URL ?? "http://localhost:8000";
// Where the server can reach public media (container: http://s3:9000/<bucket>/public).
const mediaInternal =
  process.env.MEDIA_INTERNAL_URL ??
  process.env.MEDIA_PUBLIC_BASE_URL ??
  "http://localhost:9000/ecommerce-media/public";

// Scoped to src/ so the dev watcher never walks node_modules (inotify limits in the container).
const CN = { cwd: path.resolve("src"), content: ["**/*.{ts,tsx}"], out: "lib/cn-tables.ts" };

const nextConfig: NextConfig = {
  // Separate output for host-side production builds (make lighthouse), so they never touch the
  // dev container's .next/ on the shared bind mount.
  distDir: process.env.NEXT_DIST_DIR || ".next",
  cacheComponents: true,
  partialPrefetching: true,
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  images: {
    loaderFile: "./src/lib/image-loader.ts",
    formats: ["image/avif", "image/webp"],
    deviceSizes: [375, 480, 640, 768, 1024, 1280, 1440, 1920, 2560],
    imageSizes: [96, 160, 240, 320, 400],
    qualities: [65, 70, 75],
    localPatterns: [{ pathname: "/media/**" }],
    minimumCacheTTL: 60 * 60 * 24 * 30,
  },
  async rewrites() {
    return [
      // Same-origin media (lib/media.ts). In production a CDN in front of Caddy serves these.
      { source: "/media/:path*", destination: `${mediaInternal}/:path*` },
      // Lets `next dev` on :3000 work without Caddy; behind Caddy /api never reaches Next.
      { source: "/api/v1/:path*", destination: `${internalApi}/api/v1/:path*/` },
    ];
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

/**
 * `cn` merge tables fitted to our sources and @theme scales (src/lib/cn-tables.ts, generated and
 * committed). Unlike the stock tables they know custom scales, so cn("text-display-xl",
 * "text-text-muted") keeps the size, and they ship less JS. Regenerated on dev and build.
 */
export default withCn(nextConfig, CN);
