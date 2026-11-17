import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="container-page grid min-h-[60vh] place-items-center py-section text-center">
      <div className="max-w-xl">
        <p className="eyebrow text-text-muted">Page not found</p>
        <h1 className="mt-4 font-display text-display-xl">A loose thread</h1>
        <span aria-hidden className="thread mx-auto mt-6 w-20 animate-thread text-ornament" />
        <p className="mt-6 text-body-lg text-text-muted">
          We couldn&apos;t find that page. Some collection pages are still being stitched together.
        </p>
        <Button asChild className="mt-10">
          <Link href="/">Return home</Link>
        </Button>
      </div>
    </div>
  );
}
