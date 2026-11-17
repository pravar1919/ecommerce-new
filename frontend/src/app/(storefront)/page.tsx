import type { Metadata } from "next";
import { Fragment, Suspense } from "react";

import { BlockRenderer } from "@/components/editorial/block-renderer";
import { ShowroomSection } from "@/components/showroom/showroom-section";
import { Skeleton } from "@/components/ui/skeleton";
import { resolveBrand } from "@/config/brand";
import { getPage, getSiteSettings } from "@/lib/api/server";

export async function generateMetadata(): Promise<Metadata> {
  const [{ page }, settings] = await Promise.all([getPage("home"), getSiteSettings()]);
  const brand = resolveBrand(settings);
  const title =
    page?.seo.title || settings?.seo_title || `${brand.name}${brand.tagline ? ` · ${brand.tagline}` : ""}`;
  const description = page?.seo.description || settings?.seo_description || brand.tagline || undefined;
  const og = page?.seo.og_image;
  return {
    title: { absolute: title },
    description,
    alternates: { canonical: "/" },
    openGraph: {
      title,
      description,
      type: "website",
      siteName: brand.name,
      images: og
        ? [{ url: og.url, width: og.width ?? undefined, height: og.height ?? undefined, alt: og.alt }]
        : undefined,
    },
  };
}

async function HomeContent() {
  const [{ page }, settings] = await Promise.all([getPage("home"), getSiteSettings()]);
  const brand = resolveBrand(settings);
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:8080";
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: settings?.legal_name || brand.name,
    url: siteUrl,
    sameAs: settings?.social_links.map((s) => s.url) ?? [],
  };
  return (
    <>
      <h1 className="sr-only">
        {brand.name}
        {brand.tagline ? `: ${brand.tagline}` : ""}
      </h1>
      {page ? (
        page.blocks.map((block) => (
          <Fragment key={block.id}>
            <BlockRenderer block={block} />
            {/* The virtual salon follows the category mosaic (frontend-placed until it is a CMS block). */}
            {block.type === "category_grid" && <ShowroomSection />}
          </Fragment>
        ))
      ) : (
        <div className="container-page py-section text-center">
          <p className="font-display text-display-md">The collection is being prepared.</p>
          <p className="mt-4 text-text-muted">Please check back shortly.</p>
        </div>
      )}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }}
      />
    </>
  );
}

function HomeSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading">
      <Skeleton className="h-svh min-h-[34rem] w-full" />
      <div className="container-page grid grid-cols-2 gap-gutter py-section-sm md:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="aspect-[4/5]" />
        ))}
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<HomeSkeleton />}>
      <HomeContent />
    </Suspense>
  );
}
