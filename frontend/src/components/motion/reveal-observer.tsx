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

  // Lens reveal ([data-lens], see globals.css): one delegated listener feeds the pointer position.
  useEffect(() => {
    let lens: HTMLElement | null = null;
    const onMove = (e: PointerEvent) => {
      if (e.pointerType !== "mouse") return;
      const el = (e.target as Element | null)?.closest?.<HTMLElement>("[data-lens]") ?? null;
      if (el !== lens) {
        lens?.removeAttribute("data-lens-on");
        lens = el;
        lens?.setAttribute("data-lens-on", "");
      }
      if (!el) return;
      const r = el.getBoundingClientRect();
      const x = `${e.clientX - r.left}px`;
      const y = `${e.clientY - r.top}px`;
      el.style.setProperty("--lens-x", x);
      el.style.setProperty("--lens-y", y);
      el.style.setProperty("--lens-tx", x);
      el.style.setProperty("--lens-ty", y);
    };
    const onLeave = () => {
      lens?.removeAttribute("data-lens-on");
      lens = null;
    };
    document.addEventListener("pointermove", onMove, { passive: true });
    document.documentElement.addEventListener("mouseleave", onLeave);
    return () => {
      document.removeEventListener("pointermove", onMove);
      document.documentElement.removeEventListener("mouseleave", onLeave);
    };
  }, []);
  return null;
}
