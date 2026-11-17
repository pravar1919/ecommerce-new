"use client";

import { Button } from "@/components/ui/button";

export default function StorefrontError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div role="alert" className="container-page grid min-h-[50vh] place-items-center py-section text-center">
      <div className="max-w-lg">
        <h1 className="font-display text-display-lg">Something came undone</h1>
        <p className="mt-5 text-body-lg text-text-muted">Please try again in a moment.</p>
        <Button className="mt-8" onClick={reset}>
          Try again
        </Button>
      </div>
    </div>
  );
}
