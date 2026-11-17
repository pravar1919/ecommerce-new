import { Bodoni_Moda, Hanken_Grotesk } from "next/font/google";

/** Self-hosted at build (next/font). Bodoni Moda includes its optical-size axis for large display. */
export const bodoni = Bodoni_Moda({
  subsets: ["latin"],
  axes: ["opsz"],
  style: ["normal", "italic"],
  display: "swap",
  variable: "--font-bodoni",
  // No `fallback` here: next/font emits it unquoted and "Bodoni 72" invalidates the whole
  // font-family. The fallback stack lives (quoted) in styles/tokens.css.
});

export const hanken = Hanken_Grotesk({
  // `subsets` only controls preloading; latin-ext still loads on demand through unicode-range.
  subsets: ["latin"],
  display: "swap",
  variable: "--font-hanken",
});
