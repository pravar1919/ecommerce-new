import { timingSafeEqual } from "node:crypto";

import { revalidateTag } from "next/cache";
import { type NextRequest, NextResponse } from "next/server";

/** On-demand revalidation, called by Django after content publishes (common/tasks.py). */
export async function POST(request: NextRequest) {
  const secret = process.env.REVALIDATE_SECRET ?? "";
  const given = request.headers.get("x-revalidate-secret") ?? "";
  const ok =
    secret.length > 0 &&
    given.length === secret.length &&
    timingSafeEqual(Buffer.from(given), Buffer.from(secret));
  if (!ok)
    return NextResponse.json({ error: { code: "permission_denied", message: "Forbidden" } }, { status: 403 });

  let tags: unknown;
  try {
    ({ tags } = await request.json());
  } catch {
    tags = null;
  }
  if (
    !Array.isArray(tags) ||
    tags.length === 0 ||
    tags.length > 50 ||
    !tags.every((t) => typeof t === "string" && t.length <= 256)
  ) {
    return NextResponse.json(
      { error: { code: "validation_error", message: "Expected {tags: string[]}" } },
      { status: 400 },
    );
  }
  for (const tag of tags as string[]) revalidateTag(tag, "max");
  return NextResponse.json({ revalidated: tags });
}
