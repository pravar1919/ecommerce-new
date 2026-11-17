import Link from "next/link";

export default function RootNotFound() {
  return (
    <main className="grid min-h-dvh place-items-center p-8 text-center">
      <div>
        <h1 className="font-display text-display-lg">Page not found</h1>
        <Link href="/" className="eyebrow mt-6 inline-block underline underline-offset-4">
          Return home
        </Link>
      </div>
    </main>
  );
}
