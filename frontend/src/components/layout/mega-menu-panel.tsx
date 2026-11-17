"use client";

import Link from "next/link";
import { NavigationMenu } from "radix-ui";

import { CmsImage } from "@/components/media/cms-image";
import type { Navigation } from "@/lib/api/types";
import { routes } from "@/lib/routes";

import { NAV_TRIGGER } from "./nav-styles";

/**
 * Desktop mega-menu (Radix NavigationMenu: roving focus, Esc to close, hover + keyboard).
 * Panels list sub-categories, live edits and up to two editorial tiles from the CMS.
 * Loaded only on desktop viewports by MegaMenu (mega-menu.tsx).
 */
export default function MegaMenuPanel({ nav }: { nav: Navigation }) {
  return (
    <NavigationMenu.Root aria-label="Main" className="hidden lg:block" delayDuration={120}>
      <NavigationMenu.List className="flex items-center gap-1">
        {nav.items.map((item) => {
          const hasPanel = item.children.length > 0 || item.features.length > 0;
          const trigger = NAV_TRIGGER;
          if (!hasPanel) {
            return (
              <NavigationMenu.Item key={item.id}>
                <NavigationMenu.Link asChild>
                  <Link href={routes.category(item.path)} className={trigger}>
                    {item.name}
                  </Link>
                </NavigationMenu.Link>
              </NavigationMenu.Item>
            );
          }
          return (
            <NavigationMenu.Item key={item.id}>
              <NavigationMenu.Trigger className={trigger}>{item.name}</NavigationMenu.Trigger>
              <NavigationMenu.Content className="data-[motion^=from-]:animate-in data-[motion^=from-]:fade-in data-[motion^=to-]:animate-out data-[motion^=to-]:fade-out">
                <div className="container-page grid-editorial gap-y-8 py-10">
                  <div className="col-span-3">
                    <p className="eyebrow text-text-muted">{item.eyebrow || item.name}</p>
                    <ul className="mt-5 space-y-3">
                      <li>
                        <NavigationMenu.Link asChild>
                          <Link
                            href={routes.category(item.path)}
                            className="font-display text-display-md hover:text-primary"
                          >
                            All {item.name}
                          </Link>
                        </NavigationMenu.Link>
                      </li>
                      {item.children.map((c) => (
                        <li key={c.id}>
                          <NavigationMenu.Link asChild>
                            <Link
                              href={routes.category(c.path)}
                              className="text-body-lg hover:underline hover:underline-offset-4"
                            >
                              {c.name}
                            </Link>
                          </NavigationMenu.Link>
                        </li>
                      ))}
                    </ul>
                  </div>
                  {nav.collections.length > 0 && (
                    <div className="col-span-3">
                      <p className="eyebrow text-text-muted">Edits</p>
                      <ul className="mt-5 space-y-3">
                        {nav.collections.map((c) => (
                          <li key={c.slug}>
                            <NavigationMenu.Link asChild>
                              <Link
                                href={routes.collection(c.slug)}
                                className="text-body-lg hover:underline hover:underline-offset-4"
                              >
                                {c.name}
                              </Link>
                            </NavigationMenu.Link>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <ul className="col-span-6 col-start-7 grid grid-cols-2 gap-gutter">
                    {item.features.map((f) => (
                      <li key={f.href}>
                        <NavigationMenu.Link asChild>
                          <Link href={f.href} className="group/tile block">
                            <CmsImage media={f.media} ratio="4/5" sizes="(min-width: 1440px) 340px, 22vw" />
                            {f.eyebrow && <p className="eyebrow mt-3 text-text-muted">{f.eyebrow}</p>}
                            <p className="mt-1 font-display text-heading group-hover/tile:underline group-hover/tile:underline-offset-4">
                              {f.title}
                            </p>
                          </Link>
                        </NavigationMenu.Link>
                      </li>
                    ))}
                  </ul>
                </div>
              </NavigationMenu.Content>
            </NavigationMenu.Item>
          );
        })}
      </NavigationMenu.List>
      <div className="absolute inset-x-0 top-full">
        <NavigationMenu.Viewport className="relative h-(--radix-navigation-menu-viewport-height) w-full overflow-hidden border-b bg-surface shadow-overlay transition-[height] duration-(--dur-base) ease-standard data-[state=closed]:animate-out data-[state=closed]:fade-out data-[state=open]:animate-in data-[state=open]:fade-in" />
      </div>
    </NavigationMenu.Root>
  );
}
