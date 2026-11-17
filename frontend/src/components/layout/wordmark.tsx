import Link from "next/link";

import { showDevPill, type BrandConfig } from "@/config/brand";
import { cn } from "@/lib/utils";

/**
 * Plain wordmark set in the display face (dev identity has no symbol, brand-identity.md).
 * The name always comes from BrandConfig; a DEV pill marks the temporary identity.
 */
export function Wordmark({ brand, className }: { brand: BrandConfig; className?: string }) {
  const dev = showDevPill(brand);
  return (
    <Link href="/" className={cn("group inline-flex min-h-11 items-center gap-2", className)}>
      {/* Accessible name comes from the visible text (WCAG 2.5.3 Label in Name), plus ", home". */}
      <span className="font-display text-[1.375rem] leading-none tracking-[0.18em] uppercase lg:text-[1.75rem]">
        {brand.name}
      </span>
      {dev && (
        <span
          className="rounded-pill border border-current px-1.5 py-px text-[0.625rem] leading-tight font-semibold tracking-[0.12em]"
          title="Development identity: brand name not yet approved"
        >
          DEV
        </span>
      )}
      <span className="sr-only">, home</span>
    </Link>
  );
}
