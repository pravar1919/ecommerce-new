"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { api, errorMessage } from "@/lib/api/client";

/** Confirms only on an explicit click: mail scanners that prefetch links must not opt people in. */
export function ConfirmSubscription({ token }: { token: string }) {
  const [state, setState] = useState<"idle" | "busy" | "done" | "error">("idle");
  const [message, setMessage] = useState("");
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (state === "done" || state === "error") heading.current?.focus();
  }, [state]);

  async function confirm() {
    setState("busy");
    const { error, response } = await api.POST("/api/v1/cms/newsletter/confirm/", { body: { token } });
    if (response.ok) setState("done");
    else {
      setMessage(errorMessage(error, "This link is invalid or has expired."));
      setState("error");
    }
  }

  if (!token) {
    return <p className="text-body-lg">This confirmation link is incomplete.</p>;
  }
  return (
    <div className="max-w-lg text-center" aria-live="polite">
      <h1 ref={heading} tabIndex={-1} className="font-display text-display-lg outline-none">
        {state === "done"
          ? "You're subscribed"
          : state === "error"
            ? "We couldn't confirm that"
            : "Confirm your subscription"}
      </h1>
      <p className="mt-5 text-body-lg text-text-muted">
        {state === "done"
          ? "Thank you. We'll write when there's something worth sharing."
          : state === "error"
            ? message
            : "One click and you're on the list for new edits."}
      </p>
      <div className="mt-10">
        {state === "done" || state === "error" ? (
          <Button asChild variant="secondary">
            <Link href="/">Back to the homepage</Link>
          </Button>
        ) : (
          <Button onClick={confirm} loading={state === "busy"}>
            Confirm subscription
          </Button>
        )}
      </div>
    </div>
  );
}
