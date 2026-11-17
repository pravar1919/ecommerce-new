"use client";

import { useEffect, useState, useSyncExternalStore, type RefObject } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";

function subscribe(cb: () => void) {
  const mq = window.matchMedia(QUERY);
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
}

/** true only on the client when the user has NOT requested reduced motion. SSR → false. */
export function useMotionOk(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => !window.matchMedia(QUERY).matches,
    () => false,
  );
}

const FINE = "(pointer: fine) and (hover: hover)";

export function useFinePointer(): boolean {
  return useSyncExternalStore(
    (cb) => {
      const mq = window.matchMedia(FINE);
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    () => window.matchMedia(FINE).matches,
    () => false,
  );
}

/**
 * true once `ref` comes within ~35% of a viewport below the fold, when `enabled`. Elements already
 * on screen at hydration never arm, so they are not re-animated. Motion wrappers use it to keep
 * their lazily imported libraries (motion, GSAP) out of the first-load JS.
 */
export function useNearViewport(ref: RefObject<HTMLElement | null>, enabled: boolean): boolean {
  const [armed, setArmed] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!enabled || armed || !el) return;
    if (el.getBoundingClientRect().top < window.innerHeight) return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setArmed(true);
          io.disconnect();
        }
      },
      { rootMargin: "0px 0px 35% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [ref, enabled, armed]);
  return armed;
}

/**
 * true once the page has fully loaded and the browser is idle. For purely decorative work that
 * must never compete with first-load JS or the LCP (e.g. animated film grain).
 */
export function useAfterLoadIdle(enabled = true): boolean {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!enabled || ready) return;
    let idle: number | undefined;
    const schedule = () => {
      idle =
        typeof window.requestIdleCallback === "function"
          ? window.requestIdleCallback(() => setReady(true), { timeout: 3000 })
          : window.setTimeout(() => setReady(true), 300);
    };
    if (document.readyState === "complete") schedule();
    else window.addEventListener("load", schedule, { once: true });
    return () => {
      window.removeEventListener("load", schedule);
      if (idle === undefined) return;
      if (typeof window.cancelIdleCallback === "function") window.cancelIdleCallback(idle);
      else window.clearTimeout(idle);
    };
  }, [enabled, ready]);
  return ready;
}
