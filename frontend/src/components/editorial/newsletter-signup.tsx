"use client";

import { useId, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { api, errorMessage, fieldErrors } from "@/lib/api/client";

type Props = { headline: string; body?: string; eyebrow?: string; consentText?: string; headingId: string };

type State =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "done" }
  | { kind: "error"; message: string; fields: Record<string, string[]> };

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Double opt-in signup: the API always answers 202 and emails a confirmation link. */
export function NewsletterSignup({ headline, body, eyebrow, consentText, headingId }: Props) {
  const ids = { email: useId(), consent: useId(), emailErr: useId(), consentErr: useId(), status: useId() };
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [state, setState] = useState<State>({ kind: "idle" });
  const fields = state.kind === "error" ? state.fields : {};

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const local: Record<string, string[]> = {};
    if (!EMAIL.test(email.trim())) local.email = ["Enter a valid email address."];
    if (!consent) local.consent = ["Please confirm you'd like to receive our emails."];
    if (Object.keys(local).length) {
      setState({ kind: "error", message: "Please check the highlighted fields.", fields: local });
      return;
    }
    setState({ kind: "submitting" });
    const { error, response } = await api.POST("/api/v1/cms/newsletter/", {
      body: { email: email.trim(), consent: true, source: "home" },
    });
    if (response.ok) setState({ kind: "done" });
    else
      setState({
        kind: "error",
        message: response.status === 429 ? "Too many attempts. Please try again later." : errorMessage(error),
        fields: fieldErrors(error),
      });
  }

  return (
    <div className="mx-auto max-w-2xl text-center">
      {eyebrow && <p className="eyebrow text-text-muted">{eyebrow}</p>}
      <h2 id={headingId} className="mt-4 font-display text-display-lg">
        {headline}
      </h2>
      {body && <p className="mx-auto mt-5 max-w-md text-body-lg text-text-muted">{body}</p>}

      <div id={ids.status} role="status" aria-live="polite" className="mt-8">
        {state.kind === "done" && (
          <p className="font-display text-heading">
            Almost there. Check your inbox to confirm your subscription.
          </p>
        )}
        {state.kind === "error" && <p className="text-error">{state.message}</p>}
      </div>

      {state.kind !== "done" && (
        <form noValidate onSubmit={onSubmit} className="mt-6 text-left" aria-describedby={ids.status}>
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="flex-1">
              <label htmlFor={ids.email} className="sr-only">
                Email address
              </label>
              <Input
                id={ids.email}
                type="email"
                name="email"
                autoComplete="email"
                inputMode="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-invalid={Boolean(fields.email) || undefined}
                aria-describedby={fields.email ? ids.emailErr : undefined}
                required
              />
              {fields.email && (
                <p id={ids.emailErr} className="mt-2 text-caption text-error">
                  {fields.email[0]}
                </p>
              )}
            </div>
            <Button type="submit" loading={state.kind === "submitting"}>
              Subscribe
            </Button>
          </div>
          <div className="mt-5 flex items-start gap-3">
            <Checkbox
              id={ids.consent}
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              aria-invalid={Boolean(fields.consent) || undefined}
              aria-describedby={fields.consent ? ids.consentErr : undefined}
              className="mt-0.5"
            />
            <div>
              <label htmlFor={ids.consent} className="text-body text-text-muted">
                {consentText || "I'd like to receive emails. I can unsubscribe at any time."}
              </label>
              {fields.consent && (
                <p id={ids.consentErr} className="mt-1 text-caption text-error">
                  {fields.consent[0]}
                </p>
              )}
            </div>
          </div>
        </form>
      )}
    </div>
  );
}
