import { describe, expect, it } from "vitest";

import { focalPosition, rewriteMediaUrls, toSameOriginMedia } from "@/lib/media";

const BASE = "http://localhost:9000/ecommerce-media/public";

describe("media URL rewriting", () => {
  it("maps public storage URLs to same-origin /media paths", () => {
    expect(toSameOriginMedia(`${BASE}/cms/a.png`, BASE)).toBe("/media/cms/a.png");
    expect(toSameOriginMedia(`${BASE}/cms/a.png`, `${BASE}/`)).toBe("/media/cms/a.png");
  });
  it("leaves other URLs and text alone", () => {
    expect(toSameOriginMedia("https://cdn.example.com/x.png", BASE)).toBe("https://cdn.example.com/x.png");
    expect(toSameOriginMedia(`${BASE}-evil/x.png`, BASE)).toBe(`${BASE}-evil/x.png`);
    expect(toSameOriginMedia("Heirloom", BASE)).toBe("Heirloom");
  });
  it("rewrites deeply without touching non-strings", () => {
    const out = rewriteMediaUrls({ a: [{ url: `${BASE}/p.png`, width: 10 }], b: null, c: true }, BASE);
    expect(out).toEqual({ a: [{ url: "/media/p.png", width: 10 }], b: null, c: true });
  });
  it("is a no-op without a configured base", () => {
    const v = { url: `${BASE}/p.png` };
    expect(rewriteMediaUrls(v, undefined)).toBe(v);
  });
  it("clamps focal points", () => {
    expect(focalPosition(0.7, 0.4)).toBe("70% 40%");
    expect(focalPosition(-1, 2)).toBe("0% 100%");
  });
});
