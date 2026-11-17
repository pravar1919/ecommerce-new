"use client";

import { lazy, Suspense, useRef, type ElementType } from "react";

import { cn } from "@/lib/utils";

import { useMotionOk, useNearViewport } from "./use-motion-ok";

const SplitText = lazy(() => import("@/components/vendor/react-bits/SplitText"));

type Props = { text: string; as?: "h1" | "h2" | "h3" | "p"; className?: string };

/**
 * Section-opener reveal (React Bits Split Text). The server renders a plain heading, so the text
 * is readable without JS and for crawlers. Shortly before it scrolls into view, motion-capable
 * clients swap in the animated version (GSAP loads lazily, never in the first-load bundle).
 * Headings already on screen are never re-animated.
 */
export function SplitHeading({ text, as = "h2", className }: Props) {
  const ok = useMotionOk();
  const ref = useRef<HTMLElement>(null);
  const armed = useNearViewport(ref, ok);

  const Tag = as as ElementType;
  const plain = (
    <Tag ref={ref} className={className}>
      {text}
    </Tag>
  );
  if (!armed) return plain;
  return (
    <Suspense fallback={plain}>
      <SplitText
        text={text}
        tag={as}
        className={cn("block", className)}
        splitType="words"
        effect="rise"
        mask
        delay={60}
        duration={0.9}
        ease="expo.out"
        threshold={0.2}
        textAlign="inherit"
      />
    </Suspense>
  );
}
