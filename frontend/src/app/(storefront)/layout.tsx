import { Suspense } from "react";

import { AnnouncementBar } from "@/components/layout/announcement-bar";
import { SiteChrome } from "@/components/layout/site-chrome";
import { SiteFooter, SiteFooterFallback } from "@/components/layout/site-footer";
import { SiteHeader, SiteHeaderFallback } from "@/components/layout/site-header";
import { Wordmark } from "@/components/layout/wordmark";
import { RevealObserver } from "@/components/motion/reveal-observer";
import { resolveBrand } from "@/config/brand";
import { getSiteSettings } from "@/lib/api/server";

async function Announcement() {
  const settings = await getSiteSettings();
  return settings ? <AnnouncementBar announcement={settings.announcement} /> : null;
}

/** The wordmark that signs the full-bleed homepage hero before the header slides in. */
async function HeroMark() {
  const settings = await getSiteSettings();
  return <Wordmark brand={resolveBrand(settings)} />;
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
      <SiteChrome
        mark={
          <Suspense fallback={null}>
            <HeroMark />
          </Suspense>
        }
      >
        <Suspense fallback={null}>
          <Announcement />
        </Suspense>
        <Suspense fallback={<SiteHeaderFallback />}>
          <SiteHeader />
        </Suspense>
      </SiteChrome>
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
