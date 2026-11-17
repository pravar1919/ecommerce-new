"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

/** How far the visitor scrolls before the header slides in over the immersive hero. */
const REVEAL_AT_PX = 64;

/**
 * Site chrome (announcement + header). On the homepage the campaign hero is full-bleed with no
 * chrome over it; the header slides in once the visitor scrolls (or tabs into it), and a quiet
 * wordmark (`mark`) signs the hero until then. Elsewhere the chrome is the usual sticky
 * header, and this wrapper has no box (`display: contents`) so stickiness is unaffected.
 */
export function SiteChrome({ children, mark }: { children: ReactNode; mark?: ReactNode }) {
  const immersive = usePathname() === "/";
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    if (!immersive) return;
    let frame = 0;
    const update = () => {
      frame = 0;
      setRevealed(window.scrollY > REVEAL_AT_PX);
    };
    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(update);
    };
    update(); // reloads restore mid-page scroll positions
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, [immersive]);

  if (!immersive) return <div className="contents">{children}</div>;

  return (
    <>
      <div
        data-chrome="immersive"
        data-revealed={revealed}
        className={cn(
          "fixed inset-x-0 top-0 z-40 transition-[translate,box-shadow] duration-(--dur-slow) ease-out-expo",
          // Keyboard focus reveals it; `focus-within` would also catch a clicked link that keeps
          // focus across client-side navigation and pin the header open back on the hero.
          "has-focus-visible:translate-y-0 has-focus-visible:shadow-[0_8px_30px_-12px_rgb(36_35_35/0.25)]",
          revealed ? "translate-y-0 shadow-[0_8px_30px_-12px_rgb(36_35_35/0.25)]" : "-translate-y-full",
        )}
      >
        {children}
      </div>
      {mark && (
        <div
          inert={revealed}
          aria-hidden={revealed}
          className={cn(
            "hero-mark pointer-events-none fixed inset-x-0 top-0 z-30 pt-4 lg:pt-6",
            "transition-[opacity,translate] duration-(--dur-slow) ease-out-expo",
            revealed ? "-translate-y-3 opacity-0" : "opacity-100",
          )}
        >
          <div className="container-page">
            <div className="pointer-events-auto inline-flex animate-in duration-1000 fade-in">{mark}</div>
          </div>
        </div>
      )}
    </>
  );
}
