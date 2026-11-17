import type { Price as PriceT } from "@/lib/api/types";
import { cn } from "@/lib/utils";

/** MRP strike-through, sale price, "from" for ranges. Amounts are server-formatted paise. */
export function Price({ price, className }: { price: PriceT; className?: string }) {
  return (
    <p className={cn("price flex flex-wrap items-baseline gap-x-2 text-body", className)}>
      {price.has_range && <span className="text-text-muted">From</span>}
      <span className={cn(price.on_sale && "text-primary")}>
        <span className="sr-only">{price.on_sale ? "Sale price " : "Price "}</span>
        {price.current.formatted}
      </span>
      {price.on_sale && (
        <>
          <s className="text-text-muted">
            <span className="sr-only">MRP </span>
            {price.mrp.formatted}
          </s>
          {price.discount_percent ? (
            <span className="text-caption text-primary">{price.discount_percent}% off</span>
          ) : null}
        </>
      )}
    </p>
  );
}
