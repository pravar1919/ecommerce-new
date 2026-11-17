"use client";

import createClient from "openapi-fetch";

import type { paths } from "./schema";
import type { ApiError } from "./types";

/**
 * Browser API client. Same origin (Caddy routes /api/* to Django), session cookie auth.
 * Unsafe methods send X-CSRFToken; the cookie is primed via GET /auth/csrf/ on first use.
 */
export const api = createClient<paths>({ baseUrl: "", credentials: "same-origin" });

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

let csrfPromise: Promise<string | null> | null = null;

export async function csrfToken(): Promise<string | null> {
  const existing = readCookie("csrftoken");
  if (existing) return existing;
  csrfPromise ??= api.GET("/api/v1/auth/csrf/").then(() => readCookie("csrftoken"));
  return csrfPromise;
}

api.use({
  async onRequest({ request }) {
    if (!["GET", "HEAD", "OPTIONS"].includes(request.method)) {
      const token = await csrfToken();
      if (token) request.headers.set("X-CSRFToken", token);
    }
    return request;
  },
});

export function errorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  const e = error as Partial<ApiError> | undefined;
  return e?.error?.message || fallback;
}

export function fieldErrors(error: unknown): Record<string, string[]> {
  return (error as Partial<ApiError> | undefined)?.error?.fields ?? {};
}
