"use client";

import { lazy, Suspense, type ReactNode } from "react";

import { useFinePointer, useMotionOk } from "./use-motion-ok";

const Magnet = lazy(() => import("@/components/vendor/react-bits/Magnet"));

/** Primary hero CTA only (React Bits Magnet): fine pointers, motion allowed. Otherwise inert. */
export function Magnetic({ children }: { children: ReactNode }) {
  const ok = useMotionOk();
  const fine = useFinePointer();
  if (!ok || !fine) return <>{children}</>;
  return (
    <Suspense fallback={children}>
      <Magnet padding={60} magnetStrength={4} maxOffset={10} wrapperClassName="inline-block">
        {children}
      </Magnet>
    </Suspense>
  );
}
