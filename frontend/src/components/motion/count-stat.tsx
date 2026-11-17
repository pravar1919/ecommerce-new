"use client";

import { lazy, Suspense, useRef } from "react";

import { formatCount } from "@/lib/format";

import { useMotionOk, useNearViewport } from "./use-motion-ok";

const CountUp = lazy(() => import("@/components/vendor/react-bits/CountUp"));

/**
 * Storytelling numeral (React Bits Count Up). SSR and reduced motion show the final value; the
 * counter (and `motion`) loads only as it nears the viewport.
 */
export function CountStat({ value, className }: { value: number; className?: string }) {
  const ok = useMotionOk();
  const ref = useRef<HTMLSpanElement>(null);
  const armed = useNearViewport(ref, ok);
  const plain = (
    <span ref={ref} className={className}>
      {formatCount(value)}
    </span>
  );
  if (!armed) return plain;
  return (
    <Suspense fallback={plain}>
      <span className={className}>
        <span className="sr-only">{formatCount(value)}</span>
        <span aria-hidden>
          <CountUp to={value} duration={1.6} separator="," trigger="view" easing="expo" />
        </span>
      </span>
    </Suspense>
  );
}
