/**
 * Photographer credit for licensed stock (Unsplash demo imagery). Plain text, because images often
 * sit inside links. Revealed on hover/focus of the nearest `group/img` so it never competes with
 * the photograph.
 */
export function PhotoCredit({ credit }: { credit?: string | null }) {
  if (!credit) return null;
  return (
    <span className="pointer-events-none absolute right-2 bottom-2 bg-black/45 px-1.5 py-0.5 text-[0.625rem] leading-tight text-white opacity-0 transition-opacity group-focus-within/img:opacity-100 group-hover/img:opacity-100 motion-reduce:transition-none">
      Photo: {credit} / Unsplash
    </span>
  );
}
