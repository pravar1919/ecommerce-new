import * as React from "react";
import { CheckIcon } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Native checkbox (no client JS of its own, submits with the form, keeps native validation).
 * The real input is transparent and covers a 44px hit area; the box beside it is drawn from the
 * input's state through `peer-*` variants.
 */
function Checkbox({ className, ...props }: Omit<React.ComponentProps<"input">, "type">) {
  return (
    <span className={cn("relative inline-grid size-5 shrink-0 place-items-center", className)}>
      <input
        type="checkbox"
        data-slot="checkbox"
        className="peer absolute -inset-3 z-10 cursor-pointer opacity-0 focus-visible:outline-none disabled:cursor-not-allowed"
        {...props}
      />
      <span
        aria-hidden
        className={cn(
          "grid size-5 place-items-center rounded-control border border-border-strong bg-transparent text-transparent",
          "peer-checked:bg-text peer-checked:text-bg peer-disabled:opacity-50 peer-aria-invalid:border-error",
          "peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-(--focus)",
        )}
      >
        <CheckIcon className="size-3.5" strokeWidth={2.5} />
      </span>
    </span>
  );
}

export { Checkbox };
