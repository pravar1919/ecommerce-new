#!/usr/bin/env node
/**
 * Lighthouse mobile budget check (docs/design-system.md §9). Run it against a PRODUCTION server;
 * `next dev` is unminified and unrepresentative:
 *
 *   make lighthouse                              # builds into .next-lighthouse, serves on :3100
 *   LH_BASE_URL=http://localhost:3100 npm run lighthouse -- / /some/other/path   # custom pages
 *
 * Mobile form factor, slow 4G and 4x CPU slowdown. Each page runs LH_RUNS times (default 3) and the
 * median run by LCP is judged. Exits 1 if any budget is exceeded. INP has no lab measurement, so
 * Total Blocking Time stands in for it.
 *
 * Throttling is APPLIED in the browser (LH_THROTTLING=devtools, default), not simulated. Against
 * localhost every resource arrives before first paint, so Lantern's simulation charges all JS
 * (at 4x CPU) to LCP and overstates it by ~2s. Applied throttling reflects real ordering. Against
 * a deployed origin (CI, staging), LH_THROTTLING=simulate is the lower-variance choice.
 */
import { writeFile, mkdir } from "node:fs/promises";
import path from "node:path";

import * as chromeLauncher from "chrome-launcher";
import lighthouse from "lighthouse";
import { chromium } from "playwright-core";

const BASE = (process.env.LH_BASE_URL ?? "http://localhost:3100").replace(/\/$/, "");
const RUNS = Number(process.env.LH_RUNS ?? 3);
const THROTTLING = process.env.LH_THROTTLING ?? "devtools";
const PAGES = process.argv.slice(2).length ? process.argv.slice(2) : ["/"];
const OUT = path.resolve("lighthouse");
const KB = 1024;

/** [label, measure(lhr) → number, budget, unit] */
const BUDGETS = [
  ["LCP", (r) => r.audits["largest-contentful-paint"].numericValue, 2500, "ms"],
  ["CLS", (r) => r.audits["cumulative-layout-shift"].numericValue, 0.05, ""],
  ["TBT (INP proxy)", (r) => r.audits["total-blocking-time"].numericValue, 200, "ms"],
  ["JS first load (gzip)", (r) => firstLoadJs(r), 170 * KB, "B"],
  ["Hero / LCP image", (r) => lcpImageBytes(r), 180 * KB, "B"],
];

function requests(lhr) {
  return lhr.audits["network-requests"]?.details?.items ?? [];
}
/**
 * Scripts requested before the load event: everything hydration needs, including lazy chunks it
 * pulls in. Work deliberately deferred past load (idle-time decoration) is not first-load JS.
 */
function firstLoadJs(lhr) {
  const load = lhr.audits.metrics?.details?.items?.[0]?.observedLoad ?? Infinity;
  return requests(lhr)
    .filter((q) => q.resourceType === "Script" && q.networkRequestTime <= load)
    .reduce((n, q) => n + (q.transferSize ?? 0), 0);
}
/** The LCP candidate is the highest-priority image request; 0 if the LCP element is text. */
function lcpImageBytes(lhr) {
  const imgs = requests(lhr).filter((q) => q.resourceType === "Image" && /High/.test(q.priority ?? ""));
  return imgs.reduce((m, q) => Math.max(m, q.transferSize ?? 0), 0);
}
function fmt(v, unit) {
  if (unit === "B") return `${(v / KB).toFixed(1)} KB`;
  if (unit === "ms") return `${Math.round(v)} ms`;
  return v.toFixed(3);
}

const chrome = await chromeLauncher.launch({
  chromePath: process.env.CHROME_PATH ?? chromium.executablePath(),
  chromeFlags: ["--headless=new", "--no-sandbox"],
});

let failed = false;
try {
  await mkdir(OUT, { recursive: true });
  for (const page of PAGES) {
    const url = BASE + page;
    const runs = [];
    for (let i = 0; i < RUNS; i++) {
      const result = await lighthouse(url, {
        port: chrome.port,
        output: "html",
        logLevel: "error",
        onlyCategories: ["performance", "accessibility", "best-practices", "seo"],
        throttlingMethod: THROTTLING,
      });
      if (!result?.lhr || result.lhr.runtimeError) {
        throw new Error(`${url}: ${result?.lhr?.runtimeError?.message ?? "no result"}`);
      }
      runs.push(result);
    }
    runs.sort(
      (a, b) =>
        a.lhr.audits["largest-contentful-paint"].numericValue -
        b.lhr.audits["largest-contentful-paint"].numericValue,
    );
    const { lhr, report } = runs[Math.floor(runs.length / 2)];
    const slug = page === "/" ? "home" : page.replace(/^\/|\/$/g, "").replace(/\//g, "_");
    await writeFile(path.join(OUT, `${slug}.html`), report);

    console.log(`\n${url}  (median of ${RUNS}, mobile, ${THROTTLING} throttling)`);
    const scores = Object.values(lhr.categories)
      .map((c) => `${c.title} ${Math.round(c.score * 100)}`)
      .join(" · ");
    console.log(`  ${scores}`);
    for (const [label, measure, budget, unit] of BUDGETS) {
      const v = measure(lhr);
      const ok = v <= budget;
      failed ||= !ok;
      console.log(
        `  ${ok ? "✓" : "✗"} ${label.padEnd(22)} ${fmt(v, unit).padStart(10)}  ≤ ${fmt(budget, unit)}`,
      );
    }
  }
  console.log(`\nReports: ${OUT}`);
} finally {
  await chrome.kill();
}
process.exit(failed ? 1 : 0);
