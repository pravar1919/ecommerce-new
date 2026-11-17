"use client";

import { MenuIcon } from "lucide-react";
import { lazy, Suspense, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import type { Navigation } from "@/lib/api/types";

const load = () => import("./mobile-nav-drawer");
const MobileNavDrawer = lazy(load);

/**
 * Mobile menu button. The drawer (Radix Dialog + Accordion) is a separate chunk, fetched on the
 * first sign of intent (pointer down, hover or focus) and mounted on open, so it costs nothing in
 * the first-load JS. Once mounted it stays mounted, so later opens are instant and animated.
 */
export function MobileNav({ nav, brandName }: { nav: Navigation; brandName: string }) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  return (
    <>
      <Button
        ref={button}
        variant="ghost"
        size="icon"
        className="lg:hidden"
        aria-label="Open menu"
        aria-haspopup="dialog"
        aria-expanded={open}
        onPointerDown={load}
        onPointerEnter={load}
        onFocus={load}
        onClick={() => {
          setMounted(true);
          setOpen(true);
        }}
      >
        <MenuIcon className="size-5" />
      </Button>
      {mounted && (
        <Suspense fallback={null}>
          <MobileNavDrawer
            nav={nav}
            brandName={brandName}
            open={open}
            onOpenChange={setOpen}
            returnFocusTo={button}
          />
        </Suspense>
      )}
    </>
  );
}
