"use client";

import { ArrowLeftIcon, ArrowRightIcon } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

/** Horizontal, scroll-snapping rail with previous/next controls (desktop) and native swipe. */
export function RailScroller({ label, children }: { label: string; children: ReactNode }) {
  const ref = useRef<HTMLUListElement>(null);
  const [edges, setEdges] = useState({ start: true, end: false });

  const update = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    setEdges({ start: el.scrollLeft <= 4, end: el.scrollLeft + el.clientWidth >= el.scrollWidth - 4 });
  }, []);

  useEffect(() => {
    update();
    const el = ref.current;
    el?.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      el?.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [update]);

  const page = (dir: 1 | -1) => {
    const el = ref.current;
    if (!el) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollBy({ left: dir * el.clientWidth * 0.9, behavior: reduce ? "auto" : "smooth" });
  };

  return (
    <div className="relative">
      <ul
        ref={ref}
        aria-label={label}
        className="-mx-[var(--page-margin)] no-scrollbar flex snap-x snap-mandatory scroll-px-[var(--page-margin)] gap-gutter overflow-x-auto px-[var(--page-margin)] pb-2"
      >
        {children}
      </ul>
      <div className="mt-6 hidden justify-end gap-2 md:flex">
        <button
          type="button"
          onClick={() => page(-1)}
          disabled={edges.start}
          aria-label={`Scroll ${label} back`}
          className="grid size-11 place-items-center border border-border-strong transition-opacity disabled:opacity-30"
        >
          <ArrowLeftIcon className="size-4" />
        </button>
        <button
          type="button"
          onClick={() => page(1)}
          disabled={edges.end}
          aria-label={`Scroll ${label} forward`}
          className="grid size-11 place-items-center border border-border-strong transition-opacity disabled:opacity-30"
        >
          <ArrowRightIcon className="size-4" />
        </button>
      </div>
    </div>
  );
}
