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
    // IntersectionObserver applies the target's own clip-path, and an "unveil" starts fully clipped
    // (inset 100%), so its ratio stays 0 forever. Those are watched through their unclipped parent.
    const byTarget = new Map<Element, HTMLElement[]>();
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            byTarget.get(e.target)?.forEach((el) => el.setAttribute("data-revealed", ""));
            byTarget.delete(e.target);
            io.unobserve(e.target);
          }
        }
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 },
    );
    pending().forEach((el) => {
      const target = (el.dataset.reveal === "unveil" && el.parentElement) || el;
      const list = byTarget.get(target);
      if (list) list.push(el);
      else {
        byTarget.set(target, [el]);
        io.observe(target);
      }
    });
    return () => io.disconnect();
  }, [pathname]);
  return null;
}
