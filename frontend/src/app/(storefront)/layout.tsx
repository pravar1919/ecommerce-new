import { Suspense } from "react";

import { AnnouncementBar } from "@/components/layout/announcement-bar";
import { SiteFooter, SiteFooterFallback } from "@/components/layout/site-footer";
import { SiteHeader, SiteHeaderFallback } from "@/components/layout/site-header";
import { RevealObserver } from "@/components/motion/reveal-observer";
import { getSiteSettings } from "@/lib/api/server";

async function Announcement() {
  const settings = await getSiteSettings();
  return settings ? <AnnouncementBar announcement={settings.announcement} /> : null;
}

export default function StorefrontLayout({ children }: LayoutProps<"/">) {
  return (
    <>
      <a
        href="#main"
        className="eyebrow fixed top-2 left-2 z-[60] -translate-y-24 bg-text px-4 py-3 text-bg transition-transform focus:translate-y-0"
      >
        Skip to content
      </a>
      <Suspense fallback={null}>
        <Announcement />
      </Suspense>
      <Suspense fallback={<SiteHeaderFallback />}>
        <SiteHeader />
      </Suspense>
      <main id="main" tabIndex={-1} className="outline-none">
        {children}
      </main>
      <Suspense fallback={<SiteFooterFallback />}>
        <SiteFooter />
      </Suspense>
      <RevealObserver />
    </>
  );
}
