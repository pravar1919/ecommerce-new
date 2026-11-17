"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowRightIcon, ChevronLeftIcon, ChevronRightIcon, XIcon } from "lucide-react";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type PointerEvent,
} from "react";

import { Price } from "@/components/commerce/price";
import { Button } from "@/components/ui/button";
import { focalPosition } from "@/lib/media";
import { routes } from "@/lib/routes";
import { cn } from "@/lib/utils";

import type { ShowroomWall } from "./types";

type Focus = { wall: number; index: number } | null;
type Camera = { cx: number; cy: number; cz: number };

const REST: Camera = { cx: 0, cy: 0, cz: 0 };
const pad = (n: number) => String(n).padStart(2, "0");
const mod = (n: number, m: number) => ((n % m) + m) % m;

/** Offset of `el`'s centre from the centre of `wall`, in the wall's own (untransformed) pixels. */
function offsetInWall(el: HTMLElement, wall: HTMLElement) {
  let x = el.offsetWidth / 2;
  let y = el.offsetHeight / 2;
  let node: HTMLElement | null = el;
  while (node && node !== wall) {
    x += node.offsetLeft;
    y += node.offsetTop;
    node = node.offsetParent as HTMLElement | null;
  }
  return { x: x - wall.clientWidth / 2, y: y - wall.clientHeight / 2 };
}

/**
 * The virtual salon. Walls sit on the four sides of a square room; choosing a category turns the
 * room (with a brief step back), and choosing a frame dollies the camera up to it and opens the
 * quick view beside it. Everything is CSS 3D: React only picks the angle and the camera offset.
 * Under reduced motion the global CSS reduces every transition to an instant cut.
 */
export default function ShowroomRoom({ walls, title }: { walls: ShowroomWall[]; title: string }) {
  const n = walls.length;
  const stageRef = useRef<HTMLDivElement>(null);
  const wallRefs = useRef<(HTMLDivElement | null)[]>([]);
  const frameRefs = useRef<(HTMLButtonElement | null)[][]>([]);
  const pillRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const panelHeading = useRef<HTMLHeadingElement>(null);
  const drag = useRef<{ x: number; y: number; swiped: boolean } | null>(null);

  const [turn, setTurn] = useState(0);
  const [dolly, setDolly] = useState<"a" | "b" | undefined>(undefined);
  const [focus, setFocus] = useState<Focus>(null);
  const [camera, setCamera] = useState<Camera>(REST);
  const [ink, setInk] = useState({ x: 0, w: 0 });
  const [size, setSize] = useState(0);

  const active = mod(turn, 4);
  const wall = walls[active];
  const focused = focus ? walls[focus.wall]?.products[focus.index] : undefined;

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    const ro = new ResizeObserver(() => setSize(stage.clientWidth * 10000 + stage.clientHeight));
    ro.observe(stage);
    return () => ro.disconnect();
  }, []);

  // Pill indicator follows the active wall.
  useLayoutEffect(() => {
    const pill = pillRefs.current[active];
    if (pill) setInk({ x: pill.offsetLeft, w: pill.offsetWidth });
  }, [active, size]);

  // Aim the camera: rest pose, or dolly in so the focused frame fills ~2/3 of the stage height,
  // set off to the left (desktop) or raised (mobile) to leave room for the quick view.
  useLayoutEffect(() => {
    const stage = stageRef.current;
    if (!focus || !stage) return setCamera(REST);
    const wallEl = wallRefs.current[focus.wall];
    const frame = frameRefs.current[focus.wall]?.[focus.index];
    if (!wallEl || !frame) return setCamera(REST);
    const css = getComputedStyle(stage);
    const S = stage.clientWidth;
    const H = stage.clientHeight;
    const P = S * (parseFloat(css.getPropertyValue("--kp")) || 0.75);
    const d = S * (parseFloat(css.getPropertyValue("--kd")) || 1.1);
    const narrow = S < 768;
    const dEff = (P * frame.offsetHeight) / ((narrow ? 0.4 : 0.66) * H);
    const k = dEff / P;
    const { x, y } = offsetInWall(frame, wallEl);
    setCamera({
      cx: -x + (narrow ? 0 : -0.17 * S) * k,
      cy: -y + (narrow ? -0.22 * H : 0.02 * H) * k,
      cz: Math.max(0, d - dEff),
    });
  }, [focus, size]);

  const goToWall = useCallback(
    (target: number) => {
      setFocus(null);
      let delta = mod(target - active, 4);
      if (delta === 3) delta = -1;
      if (delta === 0) return;
      setTurn((t) => t + delta);
      setDolly((dl) => (dl === "a" ? "b" : "a"));
    },
    [active],
  );

  const step = useCallback(
    (dir: 1 | -1) => {
      if (focus) {
        const count = walls[focus.wall].products.length;
        setFocus({ wall: focus.wall, index: mod(focus.index + dir, count) });
      } else {
        goToWall(mod(Math.min(active, n - 1) + dir, n));
      }
    },
    [focus, walls, goToWall, active, n],
  );

  const close = useCallback(() => {
    if (!focus) return;
    const frame = frameRefs.current[focus.wall]?.[focus.index];
    setFocus(null);
    frame?.focus({ preventScroll: true });
  }, [focus]);

  useEffect(() => {
    if (focus) panelHeading.current?.focus({ preventScroll: true });
  }, [focus]);

  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") step(1);
    else if (e.key === "ArrowLeft") step(-1);
    else return;
    e.preventDefault();
  };

  const onPointerDown = (e: PointerEvent) => {
    drag.current = { x: e.clientX, y: e.clientY, swiped: false };
  };
  const onPointerUp = (e: PointerEvent) => {
    const start = drag.current;
    if (!start) return;
    const dx = e.clientX - start.x;
    if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(e.clientY - start.y)) {
      start.swiped = true;
      step(dx < 0 ? 1 : -1);
    }
  };
  const swiped = () => {
    const s = drag.current?.swiped;
    drag.current = null;
    return s;
  };

  const style = {
    "--ry": `${turn * 90}deg`,
    "--cx": `${camera.cx}px`,
    "--cy": `${camera.cy}px`,
    "--cz": `${camera.cz}px`,
  } as CSSProperties;

  return (
    <div className="sr-wrap">
      <div
        ref={stageRef}
        className="sr-stage select-none"
        data-focus={focus ? "" : undefined}
        role="region"
        aria-roledescription="virtual showroom"
        aria-label={title}
        onKeyDown={onKeyDown}
        onPointerDown={onPointerDown}
        onPointerUp={onPointerUp}
        onPointerCancel={() => (drag.current = null)}
      >
        <div className="sr-camera" data-dolly={dolly}>
          <div className="sr-room" style={style}>
            <div aria-hidden className="sr-floor" />
            <div aria-hidden className="sr-ceiling" />
            {walls.map((w, wi) => {
              const isActive = wi === active;
              return (
                <div
                  key={w.path}
                  ref={(el) => {
                    wallRefs.current[wi] = el;
                  }}
                  className="sr-wall"
                  style={{ "--a": `${-wi * 90}deg` } as CSSProperties}
                  aria-hidden={!isActive}
                  inert={!isActive}
                >
                  <p aria-hidden className="sr-ghost">
                    {w.label}
                  </p>
                  <ul className="sr-hang" aria-label={`${w.label}, ${w.products.length} pieces`}>
                    {w.products.map((p, pi) => {
                      const img = p.primary_image;
                      const isFocused = focus?.wall === wi && focus.index === pi;
                      return (
                        <li key={p.id}>
                          <button
                            type="button"
                            ref={(el) => {
                              (frameRefs.current[wi] ??= [])[pi] = el;
                            }}
                            className="sr-frame block"
                            data-focused={isFocused ? "" : undefined}
                            aria-label={`Look closer: ${p.name}`}
                            aria-pressed={isFocused}
                            onClick={() => {
                              if (swiped()) return;
                              setFocus(isFocused ? null : { wall: wi, index: pi });
                            }}
                          >
                            <span className="sr-frame-img block">
                              {img && (
                                <Image
                                  src={img.url}
                                  alt=""
                                  fill
                                  sizes="(min-width: 768px) 360px, 240px"
                                  className="object-cover"
                                  style={{ objectPosition: focalPosition(img.focal_x, img.focal_y) }}
                                  draggable={false}
                                />
                              )}
                            </span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>

        {/* Wall title, top left */}
        <div className="sr-hud top-5 left-[var(--page-margin)] md:top-8">
          <p className="eyebrow text-ornament">
            Wall {pad(Math.min(active, n - 1) + 1)} / {pad(n)}
          </p>
          <p key={active} className="sr-swap mt-2 font-display text-display-md">
            {wall?.label}
          </p>
        </div>

        {/* Hint and wall link, top right */}
        {wall && (
          <div
            className={cn(
              "sr-hud top-5 right-[var(--page-margin)] hidden flex-col items-end gap-2 transition-opacity duration-500 md:top-8 md:flex",
              focus && "pointer-events-none opacity-0",
            )}
          >
            <p className="text-caption text-text-inverse-muted">Select a frame to look closer</p>
            <Link
              href={routes.category(wall.path)}
              className="group eyebrow inline-flex min-h-11 items-center gap-2 text-text-inverse"
            >
              Shop {wall.label}
              <ArrowRightIcon className="size-4 transition-transform duration-(--dur-base) ease-out-expo group-hover:translate-x-1" />
            </Link>
          </div>
        )}

        {/* Category pills, bottom centre */}
        <div
          className={cn(
            "sr-hud inset-x-0 bottom-5 flex items-center justify-center gap-2 px-3 transition-opacity duration-500 md:bottom-8",
            focus && "max-md:pointer-events-none max-md:opacity-0",
          )}
        >
          <button
            type="button"
            onClick={() => step(-1)}
            aria-label="Previous wall"
            className="hidden size-11 place-items-center rounded-pill border border-[rgb(248_244_236/0.18)] text-text-inverse md:grid"
          >
            <ChevronLeftIcon className="size-4" />
          </button>
          <div role="tablist" aria-label="Walls" className="sr-pills no-scrollbar max-w-full overflow-x-auto">
            <span aria-hidden className="sr-pill-ink" style={{ translate: `${ink.x}px 0`, width: ink.w }} />
            {walls.map((w, wi) => (
              <button
                key={w.path}
                ref={(el) => {
                  pillRefs.current[wi] = el;
                }}
                type="button"
                role="tab"
                aria-selected={wi === active}
                tabIndex={wi === active ? 0 : -1}
                className="sr-pill"
                onClick={() => goToWall(wi)}
              >
                {w.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => step(1)}
            aria-label="Next wall"
            className="hidden size-11 place-items-center rounded-pill border border-[rgb(248_244_236/0.18)] text-text-inverse md:grid"
          >
            <ChevronRightIcon className="size-4" />
          </button>
        </div>

        {/* Quick view */}
        <div
          role="region"
          aria-label="Quick view"
          className="sr-panel sr-hud inset-x-3 bottom-3 bg-surface p-5 text-text shadow-overlay md:inset-x-auto md:inset-y-0 md:right-[var(--page-margin)] md:my-auto md:h-fit md:w-[min(22rem,32cqw)] md:p-7"
          data-open={focused ? "" : undefined}
          inert={!focused}
          aria-hidden={!focused}
        >
          {focused && focus && (
            <>
              <div className="flex items-start justify-between gap-4">
                <p className="eyebrow text-text-muted">{focused.category.name}</p>
                <button
                  type="button"
                  onClick={close}
                  aria-label="Back to the wall"
                  className="-mt-3 -mr-3 grid size-11 shrink-0 place-items-center"
                >
                  <XIcon className="size-4" />
                </button>
              </div>
              <h3
                key={focused.id}
                ref={panelHeading}
                tabIndex={-1}
                className="sr-swap font-display text-heading outline-none md:text-display-md"
              >
                {focused.name}
              </h3>
              <Price price={focused.price} className="mt-3" />
              {focused.colours.length > 0 && (
                <p className="mt-4 flex flex-wrap items-center gap-2 text-caption text-text-muted">
                  {focused.colours.slice(0, 5).map((c) => (
                    <span key={c.slug} className="inline-flex items-center gap-1.5">
                      <span
                        aria-hidden
                        className="size-3 rounded-pill border border-[rgb(36_35_35/0.25)]"
                        style={{ backgroundColor: c.hex }}
                      />
                      {c.name}
                    </span>
                  ))}
                </p>
              )}
              {focused.is_mtm_available && (
                <p className="mt-2 text-caption text-text-muted">Made to measure available</p>
              )}
              <Button asChild className="mt-6 w-full">
                <Link href={routes.product(focused.slug)}>
                  View the piece <ArrowRightIcon />
                </Link>
              </Button>
              <div className="mt-4 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => step(-1)}
                  aria-label="Previous piece"
                  className="grid size-11 place-items-center"
                >
                  <ChevronLeftIcon className="size-4" />
                </button>
                <p className="price text-label text-text-muted">
                  {pad(focus.index + 1)} / {pad(walls[focus.wall].products.length)}
                </p>
                <button
                  type="button"
                  onClick={() => step(1)}
                  aria-label="Next piece"
                  className="grid size-11 place-items-center"
                >
                  <ChevronRightIcon className="size-4" />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
