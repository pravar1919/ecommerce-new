"use client";

import { lazy, Suspense, useRef, type ReactNode } from "react";

import { useNearViewport } from "@/components/motion/use-motion-ok";
import type { ProductLite } from "@/lib/product-lite";

const LookbookCarousel = lazy(() => import("./lookbook-carousel"));

/**
 * The server-rendered product rail (`children`) stays until the section nears the viewport; then
 * the lookbook loads and replaces it. Without JS the rail is the experience.
 */
export function LookbookIsland({
  products,
  label,
  children,
}: {
  products: ProductLite[];
  label: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const armed = useNearViewport(ref, true, { includeVisible: true });
  return (
    <div ref={ref}>
      {armed ? (
        <Suspense fallback={children}>
          <LookbookCarousel products={products} label={label} />
        </Suspense>
      ) : (
        children
      )}
    </div>
  );
}
