"use client";

import Link from "next/link";
import { PauseIcon, PlayIcon } from "lucide-react";
import { useEffect, useState } from "react";

import type { SiteSettings } from "@/lib/api/types";

const INTERVAL_MS = 5000;

/**
 * Rotating announcements. Auto-advance pauses on hover/focus and has a visible pause control
 * (WCAG 2.2.2). Under reduced motion the swap is instant (global CSS), not animated.
 */
export function AnnouncementBar({ announcement }: { announcement: SiteSettings["announcement"] }) {
  const { messages, accent } = announcement;
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [hovering, setHovering] = useState(false);
  const rotating = messages.length > 1 && !paused && !hovering;

  useEffect(() => {
    if (!rotating) return;
    const t = window.setInterval(() => setIndex((i) => (i + 1) % messages.length), INTERVAL_MS);
    return () => window.clearInterval(t);
  }, [rotating, messages.length]);

  if (!announcement.enabled || messages.length === 0) return null;
  const tone = accent === "charcoal" ? "surface-inverse" : "text-primary-fg";

  return (
    <section
      aria-label="Announcements"
      data-accent={accent}
      data-section="announcement"
      className={`relative bg-accent ${tone}`}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      onFocus={() => setHovering(true)}
      onBlur={() => setHovering(false)}
    >
      <div className="container-page flex h-10 items-center justify-center text-label tracking-[0.08em]">
        <ul className="relative h-5 w-full max-w-2xl overflow-hidden text-center">
          {messages.map((m, i) => (
            <li
              key={m.text}
              aria-hidden={i !== index}
              className="absolute inset-0 truncate transition-[opacity,transform] duration-(--dur-slow) ease-out-expo data-[active=false]:pointer-events-none data-[active=false]:translate-y-2 data-[active=false]:opacity-0"
              data-active={i === index}
            >
              {m.href ? (
                <Link
                  href={m.href}
                  tabIndex={i === index ? 0 : -1}
                  className="underline-offset-4 hover:underline"
                >
                  {m.text}
                </Link>
              ) : (
                m.text
              )}
            </li>
          ))}
        </ul>
        {messages.length > 1 && (
          <button
            type="button"
            onClick={() => setPaused((p) => !p)}
            className="absolute right-[max(var(--page-margin),calc((100vw-var(--content-max))/2+var(--page-margin)))] grid size-10 place-items-center"
            aria-label={paused ? "Resume announcements" : "Pause announcements"}
          >
            {paused ? <PlayIcon className="size-3.5" /> : <PauseIcon className="size-3.5" />}
          </button>
        )}
      </div>
    </section>
  );
}
