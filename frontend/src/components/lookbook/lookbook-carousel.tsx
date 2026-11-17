"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowLeftIcon, ArrowRightIcon } from "lucide-react";
import { useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent } from "react";

import { Price } from "@/components/commerce/price";
import { focalPosition } from "@/lib/media";
import type { ProductLite } from "@/lib/product-lite";
import { routes } from "@/lib/routes";
import { cn } from "@/lib/utils";

import "./lookbook.css";

const pad = (n: number) => String(n).padStart(2, "0");
const mod = (n: number, m: number) => ((n % m) + m) % m;

/** Signed shortest distance from `active` to `i` on a ring of `n` (so the edit loops). */
function offset(i: number, active: number, n: number) {
  let o = mod(i - active, n);
  if (o > n / 2) o -= n;
  return o;
}

/**
 * A collection edit as a depth-of-field lookbook: one piece in focus, floating, its neighbours
 * blurred behind it; the title rises in on every change and the "In this edit" list mirrors the
 * selection. Swipe, arrow keys, the list or the neighbours themselves move through the edit.
 */
export default function LookbookCarousel({ products, label }: { products: ProductLite[]; label: string }) {
  const n = products.length;
  const [active, setActive] = useState(0);
  const drag = useRef<number | null>(null);
  const current = products[active];
  const go = (i: number) => setActive(mod(i, n));

  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === "ArrowRight") go(active + 1);
    else if (e.key === "ArrowLeft") go(active - 1);
    else return;
    e.preventDefault();
  };
  const onPointerDown = (e: PointerEvent) => (drag.current = e.clientX);
  const onPointerUp = (e: PointerEvent) => {
    if (drag.current === null) return;
    const dx = e.clientX - drag.current;
    drag.current = null;
    if (Math.abs(dx) > 48) go(active + (dx < 0 ? 1 : -1));
  };

  return (
    <div
      role="region"
      aria-roledescription="carousel"
      aria-label={label}
      onKeyDown={onKeyDown}
      className="grid-editorial gap-y-10"
    >
      <div className="col-span-4 md:col-span-8 lg:col-span-8">
        <div className="lb-track" onPointerDown={onPointerDown} onPointerUp={onPointerUp}>
          <p aria-hidden key={`g${active}`} className="lb-ghost lb-fade">
            {pad(active + 1)}
          </p>
          <span aria-hidden className="lb-shadow" />
          {products.map((p, i) => {
            const o = offset(i, active, n);
            const isActive = o === 0;
            const img = p.primary_image;
            const pic = (
              <span className="lb-float relative aspect-[4/5] overflow-hidden bg-skeleton">
                {img && (
                  <Image
                    src={img.url}
                    alt={isActive ? img.alt : ""}
                    fill
                    sizes="(min-width: 1024px) 352px, (min-width: 768px) 34vw, 58vw"
                    className="object-cover"
                    style={{ objectPosition: focalPosition(img.focal_x, img.focal_y) }}
                    draggable={false}
                  />
                )}
              </span>
            );
            return (
              <div
                key={p.id}
                className="lb-item"
                data-active={isActive ? "" : undefined}
                style={{ "--o": o } as CSSProperties}
                aria-hidden={!isActive}
              >
                {isActive ? (
                  <Link href={routes.product(p.slug)} className="block" aria-label={p.name}>
                    {pic}
                  </Link>
                ) : (
                  <button
                    type="button"
                    tabIndex={-1}
                    className="block w-full cursor-pointer"
                    onClick={() => go(i)}
                    aria-label={`Show ${p.name}`}
                  >
                    {pic}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <div className="mt-6 flex flex-wrap items-end justify-between gap-6">
          <div className="min-w-0" aria-live="polite">
            <p className="eyebrow text-text-muted">
              Look {pad(active + 1)} <span aria-hidden>/</span>
              <span className="sr-only">of</span> {pad(n)}
            </p>
            <p className="mt-2 overflow-hidden pb-[0.08em] font-display text-display-md">
              <span key={current.id} className="lb-rise">
                {current.name}
              </span>
            </p>
            <div key={`p${current.id}`} className="lb-fade mt-2 flex flex-wrap items-center gap-x-6 gap-y-2">
              <Price price={current.price} />
              <Link
                href={routes.product(current.slug)}
                className="group eyebrow inline-flex min-h-11 items-center gap-2 underline underline-offset-[6px]"
              >
                View the piece
                <ArrowRightIcon
                  aria-hidden
                  className="size-4 transition-transform duration-(--dur-base) ease-out-expo group-hover:translate-x-1"
                />
              </Link>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div aria-hidden className="lb-progress flex w-28 gap-1">
              {products.map((p, i) => (
                <span
                  key={p.id}
                  className={cn("h-px grow", i === active ? "grow-[4] bg-text" : "bg-border-strong/25")}
                />
              ))}
            </div>
            <button
              type="button"
              onClick={() => go(active - 1)}
              aria-label="Previous look"
              className="grid size-11 place-items-center border border-border-strong transition-colors hover:bg-text hover:text-bg"
            >
              <ArrowLeftIcon className="size-4" />
            </button>
            <button
              type="button"
              onClick={() => go(active + 1)}
              aria-label="Next look"
              className="grid size-11 place-items-center border border-border-strong transition-colors hover:bg-text hover:text-bg"
            >
              <ArrowRightIcon className="size-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="col-span-4 md:col-span-8 lg:col-span-4 lg:col-start-9">
        <p className="eyebrow text-text-muted">In this edit</p>
        <ul className="mt-4 no-scrollbar flex gap-3 overflow-x-auto lg:flex-col lg:gap-0 lg:overflow-visible">
          {products.map((p, i) => {
            const isActive = i === active;
            const img = p.primary_image;
            return (
              <li key={p.id} className="shrink-0 lg:border-b lg:border-border">
                <button
                  type="button"
                  onClick={() => go(i)}
                  aria-current={isActive ? "true" : undefined}
                  className={cn(
                    "group flex w-full items-center gap-4 py-3 text-left transition-colors duration-(--dur-base) lg:px-3",
                    isActive ? "lg:bg-surface" : "opacity-60 hover:opacity-100",
                  )}
                >
                  <span
                    aria-hidden
                    className={cn(
                      "hidden h-14 w-px bg-primary transition-transform duration-(--dur-slow) ease-out-expo lg:block",
                      isActive ? "scale-y-100" : "scale-y-0",
                    )}
                  />
                  <span className="relative block aspect-[4/5] w-16 shrink-0 overflow-hidden bg-skeleton lg:w-14">
                    {img && (
                      <Image
                        src={img.url}
                        alt=""
                        fill
                        sizes="64px"
                        className="object-cover"
                        style={{ objectPosition: focalPosition(img.focal_x, img.focal_y) }}
                      />
                    )}
                  </span>
                  <span className="hidden min-w-0 lg:block">
                    <span className="block truncate text-[0.8125rem] font-medium tracking-[0.06em] uppercase">
                      {p.name}
                    </span>
                    <span className="price mt-1 block text-caption text-text-muted">
                      {p.price.current.formatted}
                    </span>
                  </span>
                  <span className="sr-only lg:hidden">{p.name}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
