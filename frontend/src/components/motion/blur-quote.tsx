"use client";

import { lazy, Suspense, useRef } from "react";

import { useMotionOk, useNearViewport } from "./use-motion-ok";

const BlurText = lazy(() => import("@/components/vendor/react-bits/BlurText"));

/**
 * Softer secondary reveal for testimonials (React Bits Blur Text). Plain text until it nears the
 * viewport, so `motion` stays out of the first-load JS.
 */
export function BlurQuote({ text, className }: { text: string; className?: string }) {
  const ok = useMotionOk();
  const ref = useRef<HTMLParagraphElement>(null);
  const armed = useNearViewport(ref, ok);
  const plain = (
    <p ref={ref} className={className}>
      {text}
    </p>
  );
  if (!armed) return plain;
  return (
    <Suspense fallback={plain}>
      <BlurText text={text} className={className} animateBy="words" delay={40} trigger="view" />
    </Suspense>
  );
}
