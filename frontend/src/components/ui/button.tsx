import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";

import { cn } from "@/lib/utils";

/**
 * Buttons: 2px radius, label type (uppercase, tracked), 44px minimum hit target on touch.
 * Variants per design-system.md §7: primary / secondary / ghost / link (+ inverse for dark bands).
 */
const buttonVariants = cva(
  [
    "group/button relative inline-flex shrink-0 items-center justify-center gap-2 rounded-control",
    "text-label font-medium uppercase whitespace-nowrap select-none",
    "transition-[background-color,color,border-color,opacity] duration-(--dur-fast) ease-standard",
    "disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50",
    "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  ],
  {
    variants: {
      variant: {
        primary: "bg-primary text-primary-fg hover:bg-[color-mix(in_srgb,var(--primary),black_18%)]",
        secondary: "border border-border-strong bg-transparent text-text hover:bg-text hover:text-bg",
        inverse: "bg-bg text-text hover:bg-surface",
        ghost: "bg-transparent text-text hover:bg-[color-mix(in_srgb,currentColor,transparent_92%)]",
        link: "h-auto! px-0! text-text underline decoration-1 underline-offset-[6px] hover:decoration-2",
      },
      size: {
        sm: "h-10 px-4",
        md: "h-12 px-6",
        lg: "h-14 px-8",
        icon: "size-11",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

type ButtonProps = React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
    loading?: boolean;
  };

function Button({
  className,
  variant,
  size,
  asChild = false,
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot.Root : "button";
  return (
    <Comp
      data-slot="button"
      data-variant={variant ?? "primary"}
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={asChild ? undefined : disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {asChild ? (
        children
      ) : (
        <>
          {loading && (
            <span aria-hidden className="absolute inset-x-6 bottom-2 h-px overflow-hidden">
              <span className="thread animate-thread [animation-iteration-count:infinite]" />
            </span>
          )}
          {children}
        </>
      )}
    </Comp>
  );
}

export { Button, buttonVariants };
