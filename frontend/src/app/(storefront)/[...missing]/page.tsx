import { notFound } from "next/navigation";

// This segment always renders the 404, so there is no target UI for dev-mode instant-navigation
// validation to check. Without this, every unmatched URL logs "Could not validate `instant`".
export const instant = false;

/** Any unmatched storefront URL renders the branded 404 inside the storefront chrome. */
export default function Missing() {
  notFound();
}
