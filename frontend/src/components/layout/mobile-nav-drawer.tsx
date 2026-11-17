"use client";

import Link from "next/link";
import type { RefObject } from "react";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";
import type { Navigation } from "@/lib/api/types";
import { routes } from "@/lib/routes";

type Props = {
  nav: Navigation;
  brandName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The menu button in the header, which lives outside this lazily loaded module. */
  returnFocusTo: RefObject<HTMLButtonElement | null>;
};

/**
 * Mobile navigation drawer (Radix Dialog: focus trapped, restored to the menu button on close).
 * Loaded on demand by MobileNav, so Dialog + Accordion stay out of the first-load JS.
 */
export default function MobileNavDrawer({ nav, brandName, open, onOpenChange, returnFocusTo }: Props) {
  const close = () => onOpenChange(false);
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="left"
        className="overflow-y-auto"
        // No Radix trigger here, so return focus explicitly (Safari never focuses a clicked button).
        onCloseAutoFocus={(e) => {
          e.preventDefault();
          returnFocusTo.current?.focus();
        }}
      >
        <div className="flex h-header shrink-0 items-center border-b px-5">
          <SheetTitle>{brandName}</SheetTitle>
          <SheetDescription className="sr-only">Site navigation</SheetDescription>
        </div>
        <nav aria-label="Mobile" className="shrink-0 px-5 pb-10">
          <Accordion type="single" collapsible>
            {nav.items.map((item) =>
              item.children.length > 0 ? (
                <AccordionItem key={item.id} value={item.id}>
                  <AccordionTrigger>{item.name}</AccordionTrigger>
                  <AccordionContent>
                    <ul className="space-y-1">
                      <li>
                        <Link
                          href={routes.category(item.path)}
                          onClick={close}
                          className="block py-2 font-display text-heading"
                        >
                          All {item.name}
                        </Link>
                      </li>
                      {item.children.map((c) => (
                        <li key={c.id}>
                          <Link
                            href={routes.category(c.path)}
                            onClick={close}
                            className="block py-2 text-body-lg"
                          >
                            {c.name}
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </AccordionContent>
                </AccordionItem>
              ) : (
                <div key={item.id} className="border-b">
                  <Link
                    href={routes.category(item.path)}
                    onClick={close}
                    className="eyebrow flex min-h-12 items-center"
                  >
                    {item.name}
                  </Link>
                </div>
              ),
            )}
          </Accordion>
          {nav.collections.length > 0 && (
            <div className="mt-8">
              <p className="eyebrow text-text-muted">Edits</p>
              <ul className="mt-3">
                {nav.collections.map((c) => (
                  <li key={c.slug}>
                    <Link
                      href={routes.collection(c.slug)}
                      onClick={close}
                      className="block py-2 font-display text-display-md"
                    >
                      {c.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <ul className="mt-8 space-y-1 border-t pt-6">
            <li>
              <Link href={routes.account()} onClick={close} className="eyebrow block py-2">
                Account
              </Link>
            </li>
            <li>
              <Link href={routes.wishlist()} onClick={close} className="eyebrow block py-2">
                Wishlist
              </Link>
            </li>
          </ul>
        </nav>
      </SheetContent>
    </Sheet>
  );
}
