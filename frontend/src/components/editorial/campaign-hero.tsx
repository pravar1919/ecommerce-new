"use client";

import Link from "next/link";
import { getImageProps } from "next/image";
import { ChevronLeftIcon, ChevronRightIcon, PauseIcon, PlayIcon } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { FilmGrain } from "@/components/motion/film-grain";
import { Magnetic } from "@/components/motion/magnetic";
import { useMotionOk } from "@/components/motion/use-motion-ok";
import { Button } from "@/components/ui/button";
import type { BlockOf } from "@/lib/api/types";
import { focalPosition } from "@/lib/media";
import { cn } from "@/lib/utils";

type Slide = BlockOf<"hero">["config"]["slides"][number];

/** Art-directed <picture>: 21:9 desktop crop, 4:5 mobile crop (separate asset or focal point). */
function HeroPicture({ slide, priority }: { slide: Slide; priority: boolean }) {
  // `priority` is deprecated in Next 16 and getImageProps drops it. A <picture> only ever loads one
  // candidate, so eager + high fetch priority is safe for the LCP slide.
  const common = {
    alt: slide.media.alt,
    fill: true,
    sizes: "100vw",
    loading: priority ? "eager" : "lazy",
    fetchPriority: priority ? "high" : undefined,
  } as const;
  const desktop = getImageProps({ ...common, src: slide.media.url, quality: 70 }).props;
  const mobileMedia = slide.mobile_media ?? slide.media;
  const mobile = getImageProps({ ...common, src: mobileMedia.url, quality: 65 }).props;
  return (
    <picture>
      <source media="(min-width: 768px)" srcSet={desktop.srcSet} sizes="100vw" />
      <img
        {...mobile}
        alt={slide.media.alt}
        className="absolute inset-0 size-full object-cover"
        style={{
          ...mobile.style,
          objectPosition: focalPosition(mobileMedia.focal_x, mobileMedia.focal_y),
        }}
      />
    </picture>
  );
}

/** Headline reveal is CSS-only (no JS on the LCP path): words rise from a mask, staggered. */
function Headline({ text }: { text: string }) {
  const words = text.split(/\s+/);
  return (
    <h2 className="max-w-[11ch] font-display text-[clamp(3rem,1.6rem+5.2vw,7rem)] leading-[0.92] tracking-[-0.02em] uppercase md:max-w-[15ch]">
      <span className="sr-only">{text}</span>
      <span aria-hidden className="block">
        {words.map((w, i) => (
          <span key={`${w}-${i}`}>
            <span className="inline-block overflow-hidden pb-[0.06em] align-bottom">
              <span
                className="inline-block animate-rise"
                style={{ animationDelay: `calc(${i} * var(--stagger) + 120ms)` }}
              >
                {w}
              </span>
            </span>
            {i < words.length - 1 ? " " : null}
          </span>
        ))}
      </span>
    </h2>
  );
}

export function CampaignHero({ config }: { config: BlockOf<"hero">["config"] }) {
  const { slides } = config;
  const motionOk = useMotionOk();
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [interacting, setInteracting] = useState(false);
  const [curtain, setCurtain] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const count = slides.length;
  const autoplay = Boolean(config.autoplay_ms) && count > 1 && motionOk && !paused && !interacting;

  const go = useCallback(
    (next: number) => {
      const target = (next + count) % count;
      if (!motionOk) return setIndex(target);
      setCurtain(true); // burgundy curtain wipe covers the swap
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => {
        setIndex(target);
        setCurtain(false);
      }, 300);
    },
    [count, motionOk],
  );

  useEffect(() => {
    if (!autoplay) return;
    const t = window.setTimeout(() => go(index + 1), config.autoplay_ms ?? 7000);
    return () => window.clearTimeout(t);
  }, [autoplay, index, go, config.autoplay_ms]);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  return (
    <section
      data-section="hero"
      aria-roledescription={count > 1 ? "carousel" : undefined}
      aria-label="Featured campaigns"
      className="relative"
      onMouseEnter={() => setInteracting(true)}
      onMouseLeave={() => setInteracting(false)}
      onFocusCapture={() => setInteracting(true)}
      onBlurCapture={() => setInteracting(false)}
    >
      <div className="relative aspect-[4/5] max-h-[calc(100svh-var(--header-h)-2.5rem)] min-h-[32rem] w-full overflow-hidden md:aspect-[21/9] md:min-h-0">
        {slides.map((slide, i) => {
          const active = i === index;
          const dark = slide.theme === "dark";
          return (
            <div
              key={i}
              role={count > 1 ? "group" : undefined}
              aria-roledescription={count > 1 ? "slide" : undefined}
              aria-label={count > 1 ? `${i + 1} of ${count}` : undefined}
              aria-hidden={!active}
              inert={!active}
              data-accent={slide.accent}
              className={cn(
                "absolute inset-0 transition-opacity duration-0",
                active ? "z-[2] opacity-100" : "z-0 opacity-0",
              )}
            >
              <HeroPicture slide={slide} priority={i === 0} />
              {dark && <div aria-hidden className="absolute inset-0 bg-[rgb(36_35_35/0.32)]" />}
              <FilmGrain />
              <div
                className={cn(
                  "absolute inset-x-0 bottom-0 z-[3] pb-14 md:pb-16",
                  dark ? "text-text-inverse" : "text-text",
                )}
              >
                {active && (
                  <div key={index} className="container-page">
                    {slide.eyebrow && (
                      <p className="eyebrow animate-in duration-700 fade-in">{slide.eyebrow}</p>
                    )}
                    <div className="mt-4">
                      <Headline text={slide.headline} />
                    </div>
                    <span
                      aria-hidden
                      className="thread mt-6 w-24 animate-thread text-ornament [animation-delay:600ms]"
                    />
                    {slide.subline && (
                      <p className="mt-5 max-w-md animate-in text-body-lg duration-1000 [animation-delay:500ms] [animation-fill-mode:both] fade-in">
                        {slide.subline}
                      </p>
                    )}
                    <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
                      {slide.cta && (
                        <Magnetic>
                          <Button asChild variant={dark ? "inverse" : "primary"} size="lg">
                            <Link href={slide.cta.href}>{slide.cta.label}</Link>
                          </Button>
                        </Magnetic>
                      )}
                      {slide.secondary_cta && (
                        <Link
                          href={slide.secondary_cta.href}
                          className="eyebrow inline-flex min-h-11 items-center underline underline-offset-[6px]"
                        >
                          {slide.secondary_cta.label}
                        </Link>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {/* Curtain transition (clip-path wipe), skipped under reduced motion */}
        <div
          aria-hidden
          data-accent={slides[index]?.accent}
          className="pointer-events-none absolute inset-0 z-[5] bg-accent transition-[clip-path] duration-300 ease-in-out-quart"
          style={{ clipPath: curtain ? "inset(0 0 0 0)" : "inset(0 0 0 100%)" }}
        />
      </div>

      {count > 1 && (
        <div
          className={cn(
            "absolute right-0 bottom-0 z-[6] flex items-center gap-1 pr-[var(--page-margin)] pb-3",
            slides[index]?.theme === "dark" ? "text-text-inverse" : "text-text",
          )}
        >
          <button
            type="button"
            className="grid size-11 place-items-center"
            onClick={() => go(index - 1)}
            aria-label="Previous slide"
          >
            <ChevronLeftIcon className="size-5" />
          </button>
          <p className="price min-w-12 text-center text-label" aria-live={autoplay ? "off" : "polite"}>
            {index + 1} / {count}
          </p>
          <button
            type="button"
            className="grid size-11 place-items-center"
            onClick={() => go(index + 1)}
            aria-label="Next slide"
          >
            <ChevronRightIcon className="size-5" />
          </button>
          {config.autoplay_ms && motionOk && (
            <button
              type="button"
              className="grid size-11 place-items-center"
              onClick={() => setPaused((p) => !p)}
              aria-label={paused ? "Play slideshow" : "Pause slideshow"}
            >
              {paused ? <PlayIcon className="size-4" /> : <PauseIcon className="size-4" />}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
