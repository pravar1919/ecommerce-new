import type { Metadata } from "next";
import { Suspense } from "react";

import { ConfirmSubscription } from "./confirm-subscription";

export const metadata: Metadata = { title: "Confirm subscription", robots: { index: false } };

export default function ConfirmPage({ searchParams }: PageProps<"/newsletter/confirm">) {
  return (
    <div className="container-page flex min-h-[60vh] items-center justify-center py-section">
      <Suspense fallback={<p className="text-text-muted">Confirming…</p>}>
        <Token searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

async function Token({ searchParams }: { searchParams: PageProps<"/newsletter/confirm">["searchParams"] }) {
  const { token } = await searchParams;
  return <ConfirmSubscription token={typeof token === "string" ? token : ""} />;
}
