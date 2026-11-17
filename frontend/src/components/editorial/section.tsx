import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowRightIcon } from "lucide-react";

import { SplitHeading } from "@/components/motion/split-heading";
import type { Link as CmsLink } from "@/lib/api/types";
import { cn } from "@/lib/utils";

export function sectionId(blockId: string) {
  return `s-${blockId.slice(0, 8)}`;
}

/** Shared section opener: eyebrow, display heading with the thread rule, optional CTA. */
export function SectionHeading({
  id,
  eyebrow,
  title,
  cta,
  className,
  align = "start",
}: {
  id: string;
  eyebrow?: string;
  title: string;
  cta?: CmsLink | null;
  className?: string;
  align?: "start" | "center";
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-6 md:flex-row md:items-end md:justify-between",
        align === "center" && "items-center text-center md:flex-col md:items-center",
        className,
      )}
    >
      <div>
        {eyebrow && (
          <p className="eyebrow text-text-muted" data-reveal suppressHydrationWarning>
            {eyebrow}
          </p>
        )}
        <div id={id}>
          <SplitHeading text={title} className="mt-3 font-display text-display-lg" />
        </div>
        <span
          aria-hidden
          data-reveal="thread"
          suppressHydrationWarning
          className={cn("thread mt-5 w-16 text-ornament", align === "center" && "mx-auto")}
        />
      </div>
      {cta && <ArrowLink link={cta} />}
    </div>
  );
}

export function ArrowLink({ link, className }: { link: CmsLink; className?: string }) {
  return (
    <Link
      href={link.href}
      className={cn(
        "group eyebrow inline-flex min-h-11 items-center gap-2 underline decoration-transparent underline-offset-[6px] transition-[text-decoration-color] hover:decoration-current",
        className,
      )}
    >
      {link.label}
      <ArrowRightIcon
        aria-hidden
        className="size-4 transition-transform duration-(--dur-base) ease-out-expo group-hover:translate-x-1"
      />
    </Link>
  );
}

export function Section({
  type,
  labelledBy,
  className,
  children,
  accent,
}: {
  type: string;
  labelledBy: string;
  className?: string;
  children: ReactNode;
  accent?: string;
}) {
  return (
    <section data-section={type} aria-labelledby={labelledBy} data-accent={accent} className={className}>
      {children}
    </section>
  );
}
