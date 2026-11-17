import Link from "next/link";
import { HeartIcon, SearchIcon, ShoppingBagIcon, UserIcon } from "lucide-react";
import type { ReactNode } from "react";

import { fallbackBrand, resolveBrand, type BrandConfig } from "@/config/brand";
import { getNavigation, getSiteSettings } from "@/lib/api/server";
import { routes } from "@/lib/routes";

import { MegaMenu } from "./mega-menu";
import { MobileNav } from "./mobile-nav";
import { Wordmark } from "./wordmark";

function IconLink({
  href,
  label,
  children,
  className,
}: {
  href: string;
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Link href={href} aria-label={label} className={`grid size-11 place-items-center ${className ?? ""}`}>
      {children}
    </Link>
  );
}

function HeaderFrame({ brand, nav }: { brand: BrandConfig; nav: ReactNode }) {
  return (
    <header data-section="header" className="sticky top-0 z-40 border-b bg-bg">
      <div className="container-page relative grid h-header grid-cols-[1fr_auto_1fr] items-center lg:grid-cols-[auto_1fr_auto] lg:gap-8">
        <div className="flex items-center lg:order-2 lg:justify-center">{nav}</div>
        <Wordmark brand={brand} className="justify-self-center lg:order-1 lg:justify-self-start" />
        <div className="flex items-center justify-self-end lg:order-3">
          <IconLink href={routes.search()} label="Search">
            <SearchIcon className="size-5" strokeWidth={1.5} />
          </IconLink>
          <IconLink href={routes.account()} label="Account" className="max-lg:hidden">
            <UserIcon className="size-5" strokeWidth={1.5} />
          </IconLink>
          <IconLink href={routes.wishlist()} label="Wishlist" className="max-sm:hidden">
            <HeartIcon className="size-5" strokeWidth={1.5} />
          </IconLink>
          <IconLink href={routes.bag()} label="Shopping bag">
            <ShoppingBagIcon className="size-5" strokeWidth={1.5} />
          </IconLink>
        </div>
      </div>
    </header>
  );
}

export async function SiteHeader() {
  const [settings, nav] = await Promise.all([getSiteSettings(), getNavigation()]);
  const brand = resolveBrand(settings);
  return (
    <HeaderFrame
      brand={brand}
      nav={
        nav ? (
          <>
            <MobileNav nav={nav} brandName={brand.name} />
            <MegaMenu nav={nav} />
          </>
        ) : null
      }
    />
  );
}

/** Static shell while (or if) the CMS is unavailable: same geometry, no layout shift. */
export function SiteHeaderFallback() {
  return <HeaderFrame brand={fallbackBrand} nav={null} />;
}
