"use client";

import { lazy, Suspense } from "react";

import { useAfterLoadIdle, useMotionOk } from "./use-motion-ok";

const Noise = lazy(() => import("@/components/vendor/react-bits/Noise"));

/**
 * Very low-opacity photographic grain for campaign bands (React Bits Noise). Decorative only, so
 * it loads and starts only after the page has loaded and the browser is idle.
 */
export function FilmGrain({ opacity = 0.06 }: { opacity?: number }) {
  const ok = useMotionOk();
  const idle = useAfterLoadIdle(ok);
  if (!ok || !idle) return null;
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 z-[1]">
      <Suspense fallback={null}>
        <Noise opacity={opacity} fps={12} size={2} blendMode="overlay" />
      </Suspense>
    </div>
  );
}
