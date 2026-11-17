"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

/**
 * One observer for the whole page: elements rendered with `data-reveal` (server components, no
 * client JS of their own) get `data-revealed` when they enter the viewport. Styling lives in
 * globals.css; under reduced motion nothing is pre-hidden, so this is a no-op visually.
 *
 * This runs once the layout hydrates, which can be before streamed Suspense content (the homepage
 * blocks) hydrates, so `data-revealed` may already be on a node when React reaches it. Every
 * `data-reveal` element therefore carries `suppressHydrationWarning`, and React leaves the attribute.
 */
export function RevealObserver() {
  const pathname = usePathname();
  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("data-reveal-ready", "");
    const pending = () => document.querySelectorAll<HTMLElement>("[data-reveal]:not([data-revealed])");
    if (root.dataset.motion !== "ok" || !("IntersectionObserver" in window)) {
      pending().forEach((el) => el.setAttribute("data-revealed", ""));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            e.target.setAttribute("data-revealed", "");
            io.unobserve(e.target);
          }
        }
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 },
    );
    pending().forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [pathname]);
  return null;
}
