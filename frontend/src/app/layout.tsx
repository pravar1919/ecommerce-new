import type { Metadata, Viewport } from "next";

import { MOTION_BOOTSTRAP } from "@/components/motion/motion-script";
import { fallbackBrand } from "@/config/brand";

import { bodoni, hanken } from "./fonts";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:8080";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: fallbackBrand.name, template: `%s · ${fallbackBrand.name}` },
  description: fallbackBrand.tagline || undefined,
  robots: process.env.NEXT_PUBLIC_ENVIRONMENT === "production" ? undefined : { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: "#f8f4ec",
  colorScheme: "light",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en-IN"
      data-theme={fallbackBrand.theme}
      className={`${bodoni.variable} ${hanken.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: MOTION_BOOTSTRAP }} />
      </head>
      {/* Extensions (e.g. Grammarly) add attributes to <body> before hydration. One level only. */}
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
