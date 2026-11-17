"use client";

import Link from "next/link";
import { lazy, Suspense, useSyncExternalStore } from "react";

import type { Navigation } from "@/lib/api/types";
import { routes } from "@/lib/routes";

import { NAV_TRIGGER } from "./nav-styles";

const MegaMenuPanel = lazy(() => import("./mega-menu-panel"));

const DESKTOP = "(min-width: 1024px)";

function useDesktop(): boolean {
  return useSyncExternalStore(
    (cb) => {
      const mq = window.matchMedia(DESKTOP);
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    () => window.matchMedia(DESKTOP).matches,
    () => false,
  );
}

/** Plain top-level category links: the SSR / no-JS / loading state, same geometry as the menu. */
function PlainNav({ nav }: { nav: Navigation }) {
  return (
    <nav aria-label="Main" className="hidden lg:block">
      <ul className="flex items-center gap-1">
        {nav.items.map((item) => (
          <li key={item.id}>
            <Link href={routes.category(item.path)} className={NAV_TRIGGER}>
              {item.name}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

/**
 * Desktop navigation. Servers and phones get plain links. Desktop viewports swap in the Radix
 * mega-menu (mega-menu-panel.tsx), so phones never download NavigationMenu.
 */
export function MegaMenu({ nav }: { nav: Navigation }) {
  const desktop = useDesktop();
  const plain = <PlainNav nav={nav} />;
  if (!desktop) return plain;
  return (
    <Suspense fallback={plain}>
      <MegaMenuPanel nav={nav} />
    </Suspense>
  );
}
